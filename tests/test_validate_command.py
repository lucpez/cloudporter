from pathlib import Path

from typer.testing import CliRunner

from cloudporter.cli import app

runner = CliRunner()

VALID_MANIFEST = """\
name: my-app
resources:
  - name: web-server
    type: compute
    cpu: 2
    memory_gb: 4
    os: ubuntu-22.04
"""


def test_validate_success(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    f.write_text(VALID_MANIFEST)
    result = runner.invoke(app, ["validate", str(f)])
    assert result.exit_code == 0
    assert "valid" in result.output
    assert "web-server" in result.output
    assert "compute" in result.output


def test_validate_file_not_found(tmp_path: Path) -> None:
    result = runner.invoke(app, ["validate", str(tmp_path / "nonexistent.yaml")])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_validate_invalid_yaml(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    f.write_text("{ invalid yaml: [")
    result = runner.invoke(app, ["validate", str(f)])
    assert result.exit_code == 1
    assert "YAML" in result.output


def test_validate_invalid_cpu(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    f.write_text(VALID_MANIFEST.replace("cpu: 2", "cpu: 0"))
    result = runner.invoke(app, ["validate", str(f)])
    assert result.exit_code == 1
    assert "cpu" in result.output


def test_validate_invalid_memory(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    f.write_text(VALID_MANIFEST.replace("memory_gb: 4", "memory_gb: 0"))
    result = runner.invoke(app, ["validate", str(f)])
    assert result.exit_code == 1
    assert "memory_gb" in result.output


def test_validate_invalid_os(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    f.write_text(VALID_MANIFEST.replace("os: ubuntu-22.04", "os: non-existant-os-1"))
    result = runner.invoke(app, ["validate", str(f)])
    assert result.exit_code == 1
    assert "os" in result.output


def test_validate_missing_name(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    f.write_text(VALID_MANIFEST.replace("name: my-app\n", ""))
    result = runner.invoke(app, ["validate", str(f)])
    assert result.exit_code == 1
    assert "name" in result.output


DUPLICATE_RESOURCE = """\
  - name: web-server
    type: compute
    cpu: 4
    memory_gb: 8
    os: ubuntu-24.04
"""


def test_validate_duplicate_names(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    f.write_text(VALID_MANIFEST + DUPLICATE_RESOURCE)
    result = runner.invoke(app, ["validate", str(f)])
    assert result.exit_code == 1
    assert "duplicate" in result.output
