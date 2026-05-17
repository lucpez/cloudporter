import pytest

from cloudporter.translator.azure.azurerm_virtual_machine import AzurermVirtualMachine


def _vm(
    name: str = "web-server",
    cpu: int = 2,
    memory_gb: int = 4,
    os: str = "ubuntu-22.04",
    rg_tf_name: str = "my_app",
    ssh_pub_key: str = "ssh-rsa AAAAB3Nz fake-key user@host",
) -> AzurermVirtualMachine:
    return AzurermVirtualMachine(name, cpu, memory_gb, os, rg_tf_name, ssh_pub_key)


def test_ubuntu_22_04_publisher() -> None:
    vm = _vm(os="ubuntu-22.04")
    assert vm.publisher == "Canonical"
    assert vm.sku == "22_04-lts-gen2"


def test_ubuntu_24_04_offer() -> None:
    vm = _vm(os="ubuntu-24.04")
    assert vm.offer == "ubuntu-24_04-lts"


def test_windows_server_2022_publisher() -> None:
    vm = _vm(os="windows-server-2022")
    assert vm.publisher == "MicrosoftWindowsServer"
    assert vm.os_type == "windows"


def test_size_selection_2cpu_4gb() -> None:
    vm = _vm(cpu=2, memory_gb=4)
    assert vm.vm_size == "Standard_B2s_v2"


def test_size_selection_exact_match_prefers_smallest() -> None:
    vm = _vm(cpu=2, memory_gb=1)
    assert vm.vm_size == "Standard_B2s_v2"


def test_tf_name_sanitizes_hyphens() -> None:
    vm = _vm(name="web-server")
    assert vm.tf_name == "web_server"


def test_unsupported_os_raises() -> None:
    with pytest.raises(ValueError, match="unsupported OS"):
        _vm(os="arch-linux")


def test_no_size_match_raises() -> None:
    with pytest.raises(ValueError, match="no instance type"):
        _vm(cpu=999, memory_gb=999)


def test_linux_render_contains_resource_type() -> None:
    output = _vm(os="ubuntu-22.04").render()
    assert "azurerm_linux_virtual_machine" in output


def test_windows_render_contains_resource_type() -> None:
    output = _vm(os="windows-server-2022").render()
    assert "azurerm_windows_virtual_machine" in output


def test_windows_render_uses_admin_password_variable() -> None:
    output = _vm(os="windows-server-2022").render()
    assert "var.admin_password" in output
    assert "admin_ssh_key" not in output


def test_linux_render_uses_ssh_key() -> None:
    output = _vm(os="ubuntu-22.04").render()
    assert "ssh-rsa AAAAB3Nz fake-key user@host" in output
    assert "var.admin_password" not in output


def test_render_contains_os_disk() -> None:
    linux_output = _vm(os="ubuntu-22.04").render()
    assert "os_disk" in linux_output
    assert "ReadWrite" in linux_output

    windows_output = _vm(os="windows-server-2022").render()
    assert "os_disk" in windows_output


def test_render_nic_references_subnet() -> None:
    output = _vm(rg_tf_name="my_app").render()
    assert "azurerm_virtual_network.my_app.subnet" in output


def test_render_contains_vm_size() -> None:
    output = _vm(cpu=2, memory_gb=4).render()
    assert "Standard_B2s_v2" in output


def test_render_contains_source_image_reference() -> None:
    output = _vm(os="ubuntu-22.04").render()
    assert "source_image_reference" in output
    assert "Canonical" in output
    assert "22_04-lts-gen2" in output
