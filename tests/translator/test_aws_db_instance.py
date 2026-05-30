import pytest

from cloudporter.translator.aws.aws_db_instance import (
    AwsDbInstance,
    select_instance_class,
)


def _db(
    name: str = "app-db",
    engine: str = "mysql",
    cpu: int = 2,
    memory_gb: int = 4,
    storage_gb: int = 20,
) -> AwsDbInstance:
    return AwsDbInstance(name, engine, cpu, memory_gb, storage_gb)


def test_select_instance_class_smallest_fit() -> None:
    assert select_instance_class(2, 4) == "db.t3.medium"


def test_select_instance_class_exact_cpu_memory() -> None:
    assert select_instance_class(2, 1) == "db.t3.micro"


def test_select_instance_class_no_match_raises() -> None:
    with pytest.raises(ValueError, match="no RDS instance class"):
        select_instance_class(64, 256)


def test_mysql_engine_version() -> None:
    db = _db(engine="mysql")
    assert db.engine_version == "8.0"
    assert db.engine == "mysql"


def test_postgres_engine_version() -> None:
    db = _db(engine="postgres")
    assert db.engine_version == "15"


def test_tf_name_sanitizes_hyphens() -> None:
    db = _db(name="app-db")
    assert db.tf_name == "app_db"


def test_instance_class_selected() -> None:
    db = _db(cpu=2, memory_gb=4)
    assert db.instance_class == "db.t3.medium"


def test_render_contains_resource_block() -> None:
    db = _db()
    out = db.render()
    assert 'resource "aws_db_instance" "app_db"' in out
    assert 'engine            = "mysql"' in out
    assert "var.db_password" in out
    assert "allocated_storage = 20" in out


def test_render_postgres() -> None:
    db = _db(engine="postgres")
    out = db.render()
    assert 'engine            = "postgres"' in out
    assert "engine_version" in out
