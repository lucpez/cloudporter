import json
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from cloudporter.cli import app

runner = CliRunner()


# Prevents real tofu execution in all tests
@pytest.fixture(autouse=True)  # type: ignore[untyped-decorator]
def mock_subprocess() -> Generator[MagicMock]:
    mock = MagicMock(return_value=MagicMock(returncode=0, stderr="", stdout="{}"))
    with patch("cloudporter.cli.subprocess.run", mock):
        yield mock


def _manifest_file(tmp_path: Path) -> Path:
    f = tmp_path / "manifest.yaml"
    f.write_text(VALID_MANIFEST)
    return f


VALID_MANIFEST = """\
name: my-app
resources:
  - name: web-server
    type: compute
    cpu: 2
    memory_gb: 4
    os: ubuntu-22.04
"""


def test_deploy_success(tmp_path: Path) -> None:
    f = _manifest_file(tmp_path)
    out = tmp_path / "out"
    result = runner.invoke(
        app,
        ["deploy", str(f), "--provider", "aws", "--output", str(out), "--auto-approve"],
    )
    assert result.exit_code == 0
    assert "Deploy complete" in result.output


def test_deploy_dry_run(mock_subprocess: MagicMock, tmp_path: Path) -> None:
    f = _manifest_file(tmp_path)
    out = tmp_path / "out"
    mock_subprocess.side_effect = [
        MagicMock(returncode=0, stderr=""),  # tofu init
        MagicMock(returncode=0, stdout="Plan: 1 to add, 0 to change, 0 to destroy."),
    ]
    result = runner.invoke(
        app,
        ["deploy", str(f), "--provider", "aws", "--output", str(out), "--dry-run"],
    )
    assert result.exit_code == 0
    assert "dry run complete" in result.output
    assert "Plan: 1 to add" in result.output
    cmds = [call.args[0] for call in mock_subprocess.call_args_list]
    assert any("plan" in cmd for cmd in cmds)
    assert all("apply" not in cmd for cmd in cmds)


def test_deploy_auto_approve(mock_subprocess: MagicMock, tmp_path: Path) -> None:
    f = _manifest_file(tmp_path)
    out = tmp_path / "out"
    runner.invoke(
        app,
        ["deploy", str(f), "--provider", "aws", "--output", str(out), "--auto-approve"],
    )
    cmds = [call.args[0] for call in mock_subprocess.call_args_list]
    assert any("-auto-approve" in cmd for cmd in cmds)


def test_deploy_verbose(mock_subprocess: MagicMock, tmp_path: Path) -> None:
    f = _manifest_file(tmp_path)
    out = tmp_path / "out"
    runner.invoke(
        app,
        [
            "deploy",
            str(f),
            "--provider",
            "aws",
            "--output",
            str(out),
            "--auto-approve",
            "--verbose",
        ],
    )
    # apply is the second call (after init); with --verbose capture_output=False
    apply_call = mock_subprocess.call_args_list[1]
    assert apply_call.kwargs["capture_output"] is False


def test_deploy_tofu_not_installed_init(tmp_path: Path) -> None:
    f = _manifest_file(tmp_path)
    out = tmp_path / "out"
    with patch("cloudporter.cli.subprocess.run", side_effect=FileNotFoundError):
        result = runner.invoke(
            app, ["deploy", str(f), "--provider", "aws", "--output", str(out)]
        )
    assert result.exit_code == 1
    assert "tofu is not installed" in result.output


def test_deploy_tofu_not_installed_apply(
    mock_subprocess: MagicMock, tmp_path: Path
) -> None:
    f = _manifest_file(tmp_path)
    out = tmp_path / "out"
    mock_subprocess.side_effect = [
        MagicMock(returncode=0, stderr=""),  # tofu init
        FileNotFoundError(),  # tofu apply: binary not found
    ]
    result = runner.invoke(
        app,
        ["deploy", str(f), "--provider", "aws", "--output", str(out), "--auto-approve"],
    )
    assert result.exit_code == 1
    assert "tofu is not installed" in result.output


def test_deploy_init_fails(tmp_path: Path) -> None:
    f = _manifest_file(tmp_path)
    out = tmp_path / "out"
    with patch(
        "cloudporter.cli.subprocess.run",
        return_value=MagicMock(returncode=1, stderr="init error", stdout=""),
    ):
        result = runner.invoke(
            app, ["deploy", str(f), "--provider", "aws", "--output", str(out)]
        )
    assert result.exit_code == 1


def test_deploy_apply_fails(mock_subprocess: MagicMock, tmp_path: Path) -> None:
    f = _manifest_file(tmp_path)
    out = tmp_path / "out"
    mock_subprocess.side_effect = [
        MagicMock(returncode=0, stderr=""),  # tofu init
        MagicMock(returncode=1, stderr="apply error", stdout=""),  # tofu apply
    ]
    result = runner.invoke(
        app,
        ["deploy", str(f), "--provider", "aws", "--output", str(out), "--auto-approve"],
    )
    assert result.exit_code == 1
    assert "apply error" in result.output


SHOW_JSON = json.dumps(
    {
        "values": {
            "root_module": {
                "resources": [
                    {
                        "mode": "managed",
                        "type": "aws_instance",
                        "name": "web_server",
                        "values": {"id": "i-abc123", "public_ip": "54.0.0.1"},
                    },
                    {
                        "mode": "data",
                        "type": "aws_ami",
                        "name": "web_server_ubuntu_22_04",
                        "values": {"id": "ami-xyz"},
                    },
                ]
            }
        }
    }
)


def test_deploy_resource_summary(mock_subprocess: MagicMock, tmp_path: Path) -> None:
    f = _manifest_file(tmp_path)
    out = tmp_path / "out"
    mock_subprocess.side_effect = [
        MagicMock(returncode=0, stderr=""),  # tofu init
        MagicMock(returncode=0, stderr=""),  # tofu apply
        MagicMock(returncode=0, stdout=SHOW_JSON),  # tofu show -json
    ]
    result = runner.invoke(
        app,
        ["deploy", str(f), "--provider", "aws", "--output", str(out), "--auto-approve"],
    )
    assert result.exit_code == 0
    assert "aws_instance" in result.output
    assert "web_server" in result.output
    assert "i-abc123" in result.output
    assert "aws_ami" not in result.output  # data sources filtered out


def test_deploy_resource_summary_verbose(
    mock_subprocess: MagicMock, tmp_path: Path
) -> None:
    f = _manifest_file(tmp_path)
    out = tmp_path / "out"
    mock_subprocess.side_effect = [
        MagicMock(returncode=0, stderr=""),  # tofu init
        MagicMock(returncode=0, stderr=""),  # tofu apply
        MagicMock(returncode=0, stdout=SHOW_JSON),  # tofu show -json
    ]
    result = runner.invoke(
        app,
        [
            "deploy",
            str(f),
            "--provider",
            "aws",
            "--output",
            str(out),
            "--auto-approve",
            "--verbose",
        ],
    )
    assert result.exit_code == 0
    assert "public_ip" in result.output
    assert "54.0.0.1" in result.output
