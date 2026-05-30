from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

from jinja2 import Environment, FileSystemLoader


# (sku_name, cpu, memory_gb)
# sku_name format: {tier}_{vm_size} — used directly in azurerm_*_flexible_server
class _DbSku(NamedTuple):
    cpu: int
    memory_gb: int
    sku_name: str
    arm_sku_name: str  # used by Azure Retail Prices API


_SKU_CATALOG: list[_DbSku] = [
    _DbSku(1, 2, "B_Standard_B1ms", "B1MS"),
    _DbSku(2, 4, "B_Standard_B2s", "B2S"),
    _DbSku(2, 8, "B_Standard_B2ms", "B2MS"),
    _DbSku(4, 16, "B_Standard_B4ms", "B4MS"),
    _DbSku(8, 32, "B_Standard_B8ms", "B8MS"),
    _DbSku(16, 64, "B_Standard_B16ms", "B16MS"),
]

_MYSQL_VERSION = "8.0.21"
_POSTGRES_VERSION = "14"

# Azure PostgreSQL Flexible Server only accepts specific storage_mb values
_POSTGRES_VALID_STORAGE_MB = [
    32768,
    65536,
    131072,
    262144,
    524288,
    1048576,
    2097152,
    4193280,
    4194304,
    8388608,
    16777216,
    33553408,
]

_templates = Environment(
    loader=FileSystemLoader(Path(__file__).parent), keep_trailing_newline=True
)


def _snap_postgres_storage_mb(storage_gb: int) -> int:
    storage_mb = storage_gb * 1024
    for valid in _POSTGRES_VALID_STORAGE_MB:
        if valid >= storage_mb:
            return valid
    return _POSTGRES_VALID_STORAGE_MB[-1]


def select_sku(cpu: int, memory_gb: int) -> _DbSku:
    matched = [s for s in _SKU_CATALOG if s.cpu >= cpu and s.memory_gb >= memory_gb]
    if not matched:
        raise ValueError(f"no Azure DB SKU found for cpu={cpu}, memory_gb={memory_gb}")
    return min(matched, key=lambda s: (s.cpu, s.memory_gb))


@dataclass
class AzurermDatabase:
    name: str
    engine: str
    cpu: int
    memory_gb: int
    storage_gb: int
    rg_tf_name: str
    tf_name: str = field(init=False)
    sku_name: str = field(init=False)
    arm_sku_name: str = field(init=False)

    def __post_init__(self) -> None:
        self.tf_name = self.name.replace("-", "_").replace(" ", "_")
        sku = select_sku(self.cpu, self.memory_gb)
        self.sku_name = sku.sku_name
        self.arm_sku_name = sku.arm_sku_name

    def render(self) -> str:
        if self.engine == "mysql":
            return str(
                _templates.get_template("azurerm_mysql_flexible_server.tf.j2").render(
                    tf_name=self.tf_name,
                    server_name=self.name,
                    rg_tf_name=self.rg_tf_name,
                    sku_name=self.sku_name,
                    storage_gb=self.storage_gb,
                    version=_MYSQL_VERSION,
                )
            )
        return str(
            _templates.get_template("azurerm_postgresql_flexible_server.tf.j2").render(
                tf_name=self.tf_name,
                server_name=self.name,
                rg_tf_name=self.rg_tf_name,
                sku_name=self.sku_name,
                storage_mb=_snap_postgres_storage_mb(self.storage_gb),
                version=_POSTGRES_VERSION,
            )
        )
