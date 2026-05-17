from cloudporter.translator.azure.azurerm_resource_group import AzurermResourceGroup


def test_tf_name_sanitizes_hyphens() -> None:
    rg = AzurermResourceGroup("my-app")
    assert rg.tf_name == "my_app"


def test_tf_name_sanitizes_spaces() -> None:
    rg = AzurermResourceGroup("my app")
    assert rg.tf_name == "my_app"


def test_resource_names_include_manifest_name() -> None:
    rg = AzurermResourceGroup("my-app")
    assert rg.rg_name == "my-app-rg"
    assert rg.vnet_name == "my-app-vnet"
    assert rg.subnet_name == "my-app-subnet"


def test_render_contains_resource_group() -> None:
    output = AzurermResourceGroup("my-app").render()
    assert "azurerm_resource_group" in output
    assert "my_app" in output
    assert "my-app-rg" in output


def test_render_contains_virtual_network() -> None:
    output = AzurermResourceGroup("my-app").render()
    assert "azurerm_virtual_network" in output
    assert "my-app-vnet" in output


def test_render_contains_subnet() -> None:
    output = AzurermResourceGroup("my-app").render()
    assert "subnet" in output
    assert "my-app-subnet" in output


def test_render_location_sweden_central() -> None:
    output = AzurermResourceGroup("my-app").render()
    assert "swedencentral" in output
