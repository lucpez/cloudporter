import subprocess
import warnings
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from cloudporter.manifest.schema import ComputeResource, Manifest
from cloudporter.translator.azure.azurerm_resource_group import AzurermResourceGroup
from cloudporter.translator.azure.azurerm_virtual_machine import AzurermVirtualMachine

_env = Environment(
    loader=FileSystemLoader(Path(__file__).parent), keep_trailing_newline=True
)


def _ensure_ssh_key(manifest_name: str) -> str:
    safe_name = manifest_name.replace("-", "_").replace(" ", "_")
    key_path = Path.home() / ".ssh" / f"cloudporter_{safe_name}_rsa"
    pub_key_path = key_path.with_suffix(".pub")
    if not pub_key_path.exists():
        key_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            result = subprocess.run(
                [
                    "ssh-keygen",
                    "-t",
                    "rsa",
                    "-b",
                    "4096",
                    "-f",
                    str(key_path),
                    "-N",
                    "",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                warnings.warn(f"Generated SSH key at {pub_key_path}", stacklevel=3)
            else:
                warnings.warn(
                    "could not generate SSH key; Linux VMs may fail to plan",
                    stacklevel=3,
                )
        except FileNotFoundError:
            warnings.warn(
                "ssh-keygen not found; Linux VMs may fail to plan", stacklevel=3
            )
    return pub_key_path.read_text().strip() if pub_key_path.exists() else ""


def _render_versions() -> str:
    return str(_env.get_template("versions.tf.j2").render())


def _render_variables() -> str:
    return str(_env.get_template("variables.tf.j2").render())


def _render_main(resources: list[Any], manifest_name: str, ssh_pub_key: str) -> str:
    blocks: list[str] = []

    rg = AzurermResourceGroup(manifest_name)
    blocks.append(rg.render())

    for resource in resources:
        if isinstance(resource, ComputeResource):
            vm = AzurermVirtualMachine(
                resource.name,
                resource.cpu,
                resource.memory_gb,
                resource.os,
                rg.tf_name,
                ssh_pub_key,
            )
            blocks.append(vm.render())
        else:
            warnings.warn(f"unsupported resource type: {resource.type!r}", stacklevel=2)

    return "\n".join(blocks)


def render_tofu(manifest: Manifest) -> dict[str, str]:
    has_linux = any(
        isinstance(r, ComputeResource) and "windows" not in r.os
        for r in manifest.resources
    )
    ssh_pub_key = _ensure_ssh_key(manifest.name) if has_linux else ""

    files: dict[str, str] = {
        "versions.tf": _render_versions(),
        "main.tf": _render_main(list(manifest.resources), manifest.name, ssh_pub_key),
    }

    has_windows = any(
        isinstance(r, ComputeResource) and "windows" in r.os for r in manifest.resources
    )
    if has_windows:
        files["variables.tf"] = _render_variables()

    return files
