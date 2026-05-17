from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_env = Environment(
    loader=FileSystemLoader(Path(__file__).parent), keep_trailing_newline=True
)

# (publisher, offer, sku, os_type)
_IMAGE_CATALOG: dict[str, tuple[str, str, str, str]] = {
    "ubuntu-22.04": (
        "Canonical",
        "0001-com-ubuntu-server-jammy",
        "22_04-lts-gen2",
        "linux",
    ),
    "ubuntu-24.04": ("Canonical", "ubuntu-24_04-lts", "server", "linux"),
    "windows-server-2022": (
        "MicrosoftWindowsServer",
        "WindowsServer",
        "2022-Datacenter",
        "windows",
    ),
}

# (vm_size, cpu, memory_gb)
_SIZE_CATALOG: list[tuple[str, int, int]] = [
    ("Standard_B2s_v2", 2, 4),
    ("Standard_B4s_v2", 4, 8),
    ("Standard_B8s_v2", 8, 16),
    ("Standard_B16s_v2", 16, 32),
    ("Standard_B32s_v2", 32, 64),
]


@dataclass
class AzurermVirtualMachine:
    name: str
    cpu: int
    memory_gb: int
    os: str
    rg_tf_name: str
    ssh_pub_key: str
    tf_name: str = field(init=False)
    vm_size: str = field(init=False)
    publisher: str = field(init=False)
    offer: str = field(init=False)
    sku: str = field(init=False)
    os_type: str = field(init=False)

    def __post_init__(self) -> None:
        self.tf_name = self.name.replace("-", "_").replace(" ", "_")

        if self.os not in _IMAGE_CATALOG:
            raise ValueError(f"unsupported OS: {self.os!r}")
        self.publisher, self.offer, self.sku, self.os_type = _IMAGE_CATALOG[self.os]

        matched = next(
            (
                size
                for size, c, m in _SIZE_CATALOG
                if c >= self.cpu and m >= self.memory_gb
            ),
            None,
        )
        if matched is None:
            raise ValueError(
                f"no instance type found for cpu={self.cpu}, memory_gb={self.memory_gb}"
            )
        self.vm_size = matched

    def render(self) -> str:
        template_name = (
            "azurerm_linux_virtual_machine.tf.j2"
            if self.os_type == "linux"
            else "azurerm_windows_virtual_machine.tf.j2"
        )
        return str(
            _env.get_template(template_name).render(
                tf_name=self.tf_name,
                computer_name=self.name,
                vm_size=self.vm_size,
                publisher=self.publisher,
                offer=self.offer,
                sku=self.sku,
                rg_tf_name=self.rg_tf_name,
                ssh_pub_key=self.ssh_pub_key,
            )
        )
