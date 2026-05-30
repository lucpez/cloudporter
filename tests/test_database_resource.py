from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from cloudporter.cli import app
from cloudporter.manifest.schema import DatabaseResource, Manifest

runner = CliRunner()

DB_MANIFEST = """\
name: my-app
resources:
  - name: app-db
    type: database
    engine: mysql
    cpu: 2
    memory_gb: 4
    storage_gb: 20
"""

MIXED_MANIFEST = """\
name: my-app
resources:
  - name: web-server
    type: compute
    cpu: 2
    memory_gb: 4
    os: ubuntu-22.04
  - name: app-db
    type: database
    engine: postgres
    cpu: 2
    memory_gb: 4
    storage_gb: 20
"""


# --- Schema ---


def test_database_resource_parses() -> None:
    manifest = Manifest.model_validate(
        {
            "name": "test",
            "resources": [
                {
                    "name": "db",
                    "type": "database",
                    "engine": "mysql",
                    "cpu": 2,
                    "memory_gb": 4,
                    "storage_gb": 20,
                }
            ],
        }
    )
    resource = manifest.resources[0]
    assert isinstance(resource, DatabaseResource)
    assert resource.engine == "mysql"


def test_database_resource_invalid_engine() -> None:
    with pytest.raises(Exception, match="engine"):
        Manifest.model_validate(
            {
                "name": "test",
                "resources": [
                    {
                        "name": "db",
                        "type": "database",
                        "engine": "oracle",
                        "cpu": 2,
                        "memory_gb": 4,
                        "storage_gb": 20,
                    }
                ],
            }
        )


def test_database_resource_storage_minimum() -> None:
    with pytest.raises(Exception, match="storage_gb"):
        Manifest.model_validate(
            {
                "name": "test",
                "resources": [
                    {
                        "name": "db",
                        "type": "database",
                        "engine": "mysql",
                        "cpu": 2,
                        "memory_gb": 4,
                        "storage_gb": 5,
                    }
                ],
            }
        )


def test_duplicate_name_across_resource_types() -> None:
    with pytest.raises(Exception, match="duplicate"):
        Manifest.model_validate(
            {
                "name": "test",
                "resources": [
                    {
                        "name": "shared",
                        "type": "compute",
                        "cpu": 2,
                        "memory_gb": 4,
                        "os": "ubuntu-22.04",
                    },
                    {
                        "name": "shared",
                        "type": "database",
                        "engine": "mysql",
                        "cpu": 2,
                        "memory_gb": 4,
                        "storage_gb": 20,
                    },
                ],
            }
        )


# --- AWS translate ---


def test_aws_translate_generates_db_instance(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    f.write_text(DB_MANIFEST)
    result = runner.invoke(
        app,
        ["translate", str(f), "--provider", "aws", "--output", str(tmp_path / "out")],
    )
    assert result.exit_code == 0
    main = (tmp_path / "out" / "aws" / "main.tf").read_text()
    assert 'resource "aws_db_instance"' in main
    assert "db.t3.medium" in main
    assert "var.db_password" in main


def test_aws_translate_generates_variables_tf_for_db(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    f.write_text(DB_MANIFEST)
    runner.invoke(
        app,
        ["translate", str(f), "--provider", "aws", "--output", str(tmp_path / "out")],
    )
    variables = (tmp_path / "out" / "aws" / "variables.tf").read_text()
    assert "db_password" in variables


def test_aws_translate_no_variables_tf_without_db(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    f.write_text("""\
name: my-app
resources:
  - name: web
    type: compute
    cpu: 2
    memory_gb: 4
    os: ubuntu-22.04
""")
    runner.invoke(
        app,
        ["translate", str(f), "--provider", "aws", "--output", str(tmp_path / "out")],
    )
    assert not (tmp_path / "out" / "aws" / "variables.tf").exists()


def test_aws_translate_mixed_manifest(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    f.write_text(MIXED_MANIFEST)
    runner.invoke(
        app,
        ["translate", str(f), "--provider", "aws", "--output", str(tmp_path / "out")],
    )
    main = (tmp_path / "out" / "aws" / "main.tf").read_text()
    assert "aws_instance" in main
    assert "aws_db_instance" in main


# --- Azure translate ---


def test_azure_translate_generates_mysql_server(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    f.write_text(DB_MANIFEST)
    with patch(
        "cloudporter.translator.azure._ensure_ssh_key",
        return_value="",
    ):
        result = runner.invoke(
            app,
            [
                "translate",
                str(f),
                "--provider",
                "azure",
                "--output",
                str(tmp_path / "out"),
            ],
        )
    assert result.exit_code == 0
    main = (tmp_path / "out" / "azure" / "main.tf").read_text()
    assert 'resource "azurerm_mysql_flexible_server"' in main
    assert "var.db_password" in main


def test_azure_translate_generates_postgres_server(tmp_path: Path) -> None:
    manifest = """\
name: my-app
resources:
  - name: app-db
    type: database
    engine: postgres
    cpu: 2
    memory_gb: 4
    storage_gb: 20
"""
    f = tmp_path / "manifest.yaml"
    f.write_text(manifest)
    with patch(
        "cloudporter.translator.azure._ensure_ssh_key",
        return_value="",
    ):
        runner.invoke(
            app,
            [
                "translate",
                str(f),
                "--provider",
                "azure",
                "--output",
                str(tmp_path / "out"),
            ],
        )
    main = (tmp_path / "out" / "azure" / "main.tf").read_text()
    assert 'resource "azurerm_postgresql_flexible_server"' in main


def test_azure_translate_generates_variables_tf_for_db(tmp_path: Path) -> None:
    f = tmp_path / "manifest.yaml"
    f.write_text(DB_MANIFEST)
    with patch(
        "cloudporter.translator.azure._ensure_ssh_key",
        return_value="",
    ):
        runner.invoke(
            app,
            [
                "translate",
                str(f),
                "--provider",
                "azure",
                "--output",
                str(tmp_path / "out"),
            ],
        )
    variables = (tmp_path / "out" / "azure" / "variables.tf").read_text()
    assert "db_password" in variables
