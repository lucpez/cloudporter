import pytest

from cloudporter.translator.aws.aws_ami import AwsAmi


def _ami(os: str = "ubuntu-22.04", resource_tf_name: str = "web_server") -> AwsAmi:
    return AwsAmi(os, resource_tf_name)


def test_ubuntu_22_04_owner() -> None:
    assert _ami("ubuntu-22.04").owner == "099720109477"


def test_ubuntu_24_04_owner() -> None:
    assert _ami("ubuntu-24.04").owner == "099720109477"


def test_windows_server_2022_owner() -> None:
    assert _ami("windows-server-2022").owner == "801119661308"


def test_ubuntu_22_04_name_filter() -> None:
    assert "ubuntu-jammy-22.04" in _ami("ubuntu-22.04").name_filter


def test_ubuntu_24_04_name_filter() -> None:
    assert "ubuntu-noble-24.04" in _ami("ubuntu-24.04").name_filter


def test_windows_name_filter() -> None:
    assert "Windows_Server-2022" in _ami("windows-server-2022").name_filter


def test_tf_name_includes_os_slug() -> None:
    assert _ami("ubuntu-22.04", "web_server").tf_name == "web_server_ubuntu_22_04"


def test_unsupported_os_raises() -> None:
    with pytest.raises(ValueError, match="unsupported OS"):
        _ami("arch-linux")


def test_render_contains_owner() -> None:
    assert "099720109477" in _ami("ubuntu-22.04").render()


def test_render_contains_tf_name() -> None:
    assert "web_server_ubuntu_22_04" in _ami("ubuntu-22.04", "web_server").render()
