import json

from typer.testing import CliRunner

from cloudporter.audit.auditor import Finding, audit
from cloudporter.cli import app
from cloudporter.manifest.schema import Manifest

runner = CliRunner()


def _manifest(resources: list[dict]) -> Manifest:  # type: ignore[type-arg]
    return Manifest.model_validate({"name": "test-app", "resources": resources})


_COMPUTE = {
    "name": "web",
    "type": "compute",
    "cpu": 2,
    "memory_gb": 4,
    "os": "ubuntu-22.04",
}
_DB = {
    "name": "app-db",
    "type": "database",
    "engine": "mysql",
    "cpu": 2,
    "memory_gb": 4,
    "storage_gb": 20,
}


# --- audit() unit tests ---


def test_empty_manifest_returns_error() -> None:
    manifest = _manifest([])
    findings = audit(manifest)
    assert len(findings) == 1
    assert findings[0].id == "empty-manifest"
    assert findings[0].level == "error"


def test_database_without_compute_returns_warning() -> None:
    manifest = _manifest([_DB])
    findings = audit(manifest)
    assert any(
        f.id == "database-without-compute-layer" and f.level == "warning"
        for f in findings
    )


def test_database_without_compute_sets_resource_fields() -> None:
    manifest = _manifest([_DB])
    findings = audit(manifest)
    f = next(f for f in findings if f.id == "database-without-compute-layer")
    assert f.resource == "app-db"
    assert f.resource_type == "database"


def test_database_with_compute_no_warning() -> None:
    manifest = _manifest([_COMPUTE, _DB])
    findings = audit(manifest)
    assert not any(f.id == "database-without-compute-layer" for f in findings)


def test_clean_manifest_no_findings() -> None:
    manifest = _manifest([_COMPUTE, _DB])
    assert audit(manifest) == []


def test_finding_has_id_and_detail() -> None:
    manifest = _manifest([_DB])
    findings = audit(manifest)
    for f in findings:
        assert isinstance(f, Finding)
        assert f.id
        assert f.detail


# --- CLI text format tests ---

COMPUTE_MANIFEST = """\
name: my-app
resources:
  - name: web
    type: compute
    cpu: 2
    memory_gb: 4
    os: ubuntu-22.04
  - name: app-db
    type: database
    engine: mysql
    cpu: 2
    memory_gb: 4
    storage_gb: 100
"""

DB_ONLY_MANIFEST = """\
name: my-app
resources:
  - name: app-db
    type: database
    engine: mysql
    cpu: 2
    memory_gb: 4
    storage_gb: 20
"""


def test_cli_clean_manifest_exits_0(tmp_path):  # type: ignore[no-untyped-def]
    f = tmp_path / "manifest.yaml"
    f.write_text(COMPUTE_MANIFEST)
    result = runner.invoke(app, ["audit", str(f)])
    assert result.exit_code == 0
    assert "No security issues found" in result.output


def test_cli_db_only_exits_0_with_warning(tmp_path):  # type: ignore[no-untyped-def]
    f = tmp_path / "manifest.yaml"
    f.write_text(DB_ONLY_MANIFEST)
    result = runner.invoke(app, ["audit", str(f)])
    assert result.exit_code == 0
    assert "WARN" in result.output
    assert "compute layer" in result.output


def test_cli_missing_file_exits_1(tmp_path):  # type: ignore[no-untyped-def]
    result = runner.invoke(app, ["audit", str(tmp_path / "nope.yaml")])
    assert result.exit_code == 1


# --- CLI json format tests ---


def test_cli_json_clean_manifest_exits_0(tmp_path):  # type: ignore[no-untyped-def]
    f = tmp_path / "manifest.yaml"
    f.write_text(COMPUTE_MANIFEST)
    result = runner.invoke(app, ["audit", str(f), "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data == []


def test_cli_json_warning_exits_0(tmp_path):  # type: ignore[no-untyped-def]
    f = tmp_path / "manifest.yaml"
    f.write_text(DB_ONLY_MANIFEST)
    result = runner.invoke(app, ["audit", str(f), "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["id"] == "database-without-compute-layer"
    assert data[0]["level"] == "warning"
    assert data[0]["resource"] == "app-db"
    assert data[0]["resource_type"] == "database"


def test_cli_json_has_stable_keys(tmp_path):  # type: ignore[no-untyped-def]
    f = tmp_path / "manifest.yaml"
    f.write_text(DB_ONLY_MANIFEST)
    result = runner.invoke(app, ["audit", str(f), "--format", "json"])
    data = json.loads(result.output)
    assert all(
        {"id", "level", "resource", "resource_type", "message", "detail"} <= d.keys()
        for d in data
    )
