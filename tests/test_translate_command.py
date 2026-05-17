from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from cloudporter.cli import app

runner = CliRunner()


# Prevents real tofu execution in all tests
@pytest.fixture(autouse=True)  # type: ignore[untyped-decorator]
def mock_tofu_init() -> Generator[MagicMock]:
    mock = MagicMock(return_value=MagicMock(returncode=0, stderr=""))
    with patch("cloudporter.cli.subprocess.run", mock):
        yield mock


VALID_MANIFEST = """\
name: my-app
resources:
  - name: web-server
    type: compute
    cpu: 2
    memory_gb: 4
    os: ubuntu-22.04
"""


def test_translate_success(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    out = tmp_path / "out"
    f.write_text(VALID_MANIFEST)
    result = runner.invoke(
        app, ["translate", str(f), "--provider", "aws", "--output", str(out)]
    )
    assert result.exit_code == 0
    assert (out / "aws" / "versions.tf").exists()
    assert (out / "aws" / "main.tf").exists()


def test_translate_versions_tf_content(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    out = tmp_path / "out"
    f.write_text(VALID_MANIFEST)
    runner.invoke(app, ["translate", str(f), "--provider", "aws", "--output", str(out)])
    content = (out / "aws" / "versions.tf").read_text()
    assert "hashicorp/aws" in content
    assert "us-east-1" in content


def test_translate_compute_tf_content(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    out = tmp_path / "out"
    f.write_text(VALID_MANIFEST)
    runner.invoke(app, ["translate", str(f), "--provider", "aws", "--output", str(out)])
    main = (out / "aws" / "main.tf").read_text()
    assert "aws_instance" in main
    assert "t3.medium" in main
    assert "data.aws_ami.web_server_ubuntu_22_04.id" in main
    assert "099720109477" in main
    assert "web_server_ubuntu_22_04" in main


def test_translate_custom_output(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    f.write_text(VALID_MANIFEST)
    out = tmp_path / "custom-out"
    result = runner.invoke(
        app, ["translate", str(f), "--provider", "aws", "--output", str(out)]
    )
    assert result.exit_code == 0
    assert (out / "aws" / "versions.tf").exists()


def test_translate_default_output_dir_includes_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    f = tmp_path / "manifest.yaml"
    f.write_text(VALID_MANIFEST)
    result = runner.invoke(app, ["translate", str(f), "--provider", "aws"])
    assert result.exit_code == 0
    assert (tmp_path / "my-app" / "aws" / "versions.tf").exists()


def test_translate_azure_success(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    out = tmp_path / "out"
    f.write_text(VALID_MANIFEST)
    result = runner.invoke(
        app, ["translate", str(f), "--provider", "azure", "--output", str(out)]
    )
    assert result.exit_code == 0
    assert (out / "azure" / "versions.tf").exists()
    assert (out / "azure" / "main.tf").exists()


def test_translate_invalid_yaml(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    f.write_text("{ invalid yaml: [")
    result = runner.invoke(app, ["translate", str(f), "--provider", "aws"])
    assert result.exit_code == 1
    assert "YAML" in result.output


def test_translate_invalid_manifest(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    f.write_text(VALID_MANIFEST.replace("cpu: 2", "cpu: 0"))
    result = runner.invoke(app, ["translate", str(f), "--provider", "aws"])
    assert result.exit_code == 1
    assert "cpu" in result.output


def test_translate_file_not_found(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["translate", str(tmp_path / "nope.yaml"), "--provider", "aws"]
    )
    assert result.exit_code == 1
    assert "not found" in result.output


def test_translate_unsupported_provider(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    f.write_text(VALID_MANIFEST)
    result = runner.invoke(app, ["translate", str(f), "--provider", "gcp"])
    assert result.exit_code == 1
    assert "unsupported provider" in result.output


def test_translate_no_instance_for_requirements(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    f.write_text(VALID_MANIFEST.replace("cpu: 2", "cpu: 999"))
    result = runner.invoke(app, ["translate", str(f), "--provider", "aws"])
    assert result.exit_code == 1
    assert "no instance type" in result.output


def test_translate_unsupported_os(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    f.write_text(VALID_MANIFEST.replace("os: ubuntu-22.04", "os: arch-linux"))
    result = runner.invoke(app, ["translate", str(f), "--provider", "aws"])
    assert result.exit_code == 1
    assert "unsupported OS" in result.output


SECOND_RESOURCE = """\
  - name: api-server
    type: compute
    cpu: 2
    memory_gb: 4
    os: ubuntu-22.04
"""


def test_translate_two_instances_same_os(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    out = tmp_path / "out"
    f.write_text(VALID_MANIFEST + SECOND_RESOURCE)
    result = runner.invoke(
        app, ["translate", str(f), "--provider", "aws", "--output", str(out)]
    )
    assert result.exit_code == 0
    main = (out / "aws" / "main.tf").read_text()
    assert "web_server_ubuntu_22_04" in main
    assert "api_server_ubuntu_22_04" in main
    assert main.count("data.aws_ami") == 2
    assert main.count("aws_instance") == 2


# --- test tofu init ---


def test_translate_runs_tofu_init_on_output_dir(
    mock_tofu_init: MagicMock, tmp_path: Path
) -> None:
    f = tmp_path / "manifest.yaml"
    out = tmp_path / "out"
    f.write_text(VALID_MANIFEST)
    result = runner.invoke(
        app, ["translate", str(f), "--provider", "aws", "--output", str(out)]
    )
    assert result.exit_code == 0
    assert "tofu init complete" in result.output
    _, kwargs = mock_tofu_init.call_args
    assert kwargs["cwd"] == out / "aws"


def test_translate_warns_when_tofu_not_installed(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    out = tmp_path / "out"
    f.write_text(VALID_MANIFEST)
    with patch("cloudporter.cli.subprocess.run", side_effect=FileNotFoundError):
        result = runner.invoke(
            app, ["translate", str(f), "--provider", "aws", "--output", str(out)]
        )
    assert result.exit_code == 0
    assert "tofu is not installed" in result.output


def test_translate_fails_when_tofu_init_fails(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    out = tmp_path / "out"
    f.write_text(VALID_MANIFEST)
    with patch(
        "cloudporter.cli.subprocess.run",
        return_value=MagicMock(returncode=1, stderr="some tofu error"),
    ):
        result = runner.invoke(
            app, ["translate", str(f), "--provider", "aws", "--output", str(out)]
        )
    assert result.exit_code == 1
