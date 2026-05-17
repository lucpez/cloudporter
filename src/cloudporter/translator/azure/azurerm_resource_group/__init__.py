from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_env = Environment(
    loader=FileSystemLoader(Path(__file__).parent), keep_trailing_newline=True
)


@dataclass
class AzurermResourceGroup:
    manifest_name: str
    tf_name: str = field(init=False)
    rg_name: str = field(init=False)
    vnet_name: str = field(init=False)
    subnet_name: str = field(init=False)

    def __post_init__(self) -> None:
        self.tf_name = self.manifest_name.replace("-", "_").replace(" ", "_")
        self.rg_name = f"{self.manifest_name}-rg"
        self.vnet_name = f"{self.manifest_name}-vnet"
        self.subnet_name = f"{self.manifest_name}-subnet"

    def render(self) -> str:
        return str(
            _env.get_template("azurerm_resource_group.tf.j2").render(
                tf_name=self.tf_name,
                rg_name=self.rg_name,
                vnet_name=self.vnet_name,
                subnet_name=self.subnet_name,
            )
        )
