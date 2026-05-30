import pytest

from cloudporter.translator.azure.azurerm_database import AzurermDatabase, select_sku


def _db(
    name: str = "app-db",
    engine: str = "mysql",
    cpu: int = 2,
    memory_gb: int = 4,
    storage_gb: int = 20,
    rg_tf_name: str = "my_app",
) -> AzurermDatabase:
    return AzurermDatabase(name, engine, cpu, memory_gb, storage_gb, rg_tf_name)


def test_select_sku_smallest_fit() -> None:
    sku = select_sku(2, 4)
    assert sku.sku_name == "B_Standard_B2s"


def test_select_sku_larger_requirement() -> None:
    sku = select_sku(2, 8)
    assert sku.sku_name == "B_Standard_B2ms"


def test_select_sku_no_match_raises() -> None:
    with pytest.raises(ValueError, match="no Azure DB SKU"):
        select_sku(64, 512)


def test_tf_name_sanitizes_hyphens() -> None:
    db = _db(name="app-db")
    assert db.tf_name == "app_db"


def test_sku_name_assigned() -> None:
    db = _db(cpu=2, memory_gb=4)
    assert db.sku_name == "B_Standard_B2s"


def test_arm_sku_name_assigned() -> None:
    db = _db(cpu=2, memory_gb=8)
    assert db.arm_sku_name == "B2MS"


def test_render_mysql_uses_flexible_server() -> None:
    db = _db(engine="mysql")
    out = db.render()
    assert 'resource "azurerm_mysql_flexible_server" "app_db"' in out
    assert "var.db_password" in out
    assert "size_gb = 20" in out


def test_render_postgres_uses_flexible_server() -> None:
    db = _db(engine="postgres")
    out = db.render()
    assert 'resource "azurerm_postgresql_flexible_server" "app_db"' in out
    assert "var.db_password" in out
    assert "storage_mb" in out


def test_render_references_resource_group() -> None:
    db = _db(rg_tf_name="my_app")
    out = db.render()
    assert "azurerm_resource_group.my_app" in out
