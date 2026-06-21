import pytest

from cloudporter.translator.aws.aws_instance import AwsInstance


def _instance(
    name: str = "web-server",
    cpu: int = 2,
    memory_gb: int = 4,
    ami_ref: str = "web_server_ubuntu_22_04",
    sg_tf_name: str = "web_server_sg",
) -> AwsInstance:
    return AwsInstance(name, cpu, memory_gb, ami_ref, sg_tf_name)


def test_instance_type_2cpu_4gb() -> None:
    assert _instance(cpu=2, memory_gb=4).instance_type == "t3.medium"


def test_instance_type_prefers_smallest_fit() -> None:
    assert _instance(cpu=1, memory_gb=1).instance_type == "t3.micro"


def test_tf_name_sanitizes_hyphens() -> None:
    assert _instance(name="web-server").tf_name == "web_server"


def test_tf_name_sanitizes_spaces() -> None:
    assert _instance(name="web server").tf_name == "web_server"


def test_no_instance_match_raises() -> None:
    with pytest.raises(ValueError, match="no instance type"):
        _instance(cpu=999, memory_gb=999)


def test_render_contains_aws_instance() -> None:
    assert "aws_instance" in _instance().render()


def test_render_contains_instance_type() -> None:
    assert "t3.medium" in _instance(cpu=2, memory_gb=4).render()


def test_render_contains_ami_ref() -> None:
    output = _instance(ami_ref="web_server_ubuntu_22_04").render()
    assert "data.aws_ami.web_server_ubuntu_22_04.id" in output


def test_render_two_different_names_produce_distinct_tf_names() -> None:
    a = AwsInstance("web-server", 2, 4, "web_server_ubuntu_22_04", "web_server_sg")
    b = AwsInstance("api-server", 2, 4, "api_server_ubuntu_22_04", "api_server_sg")
    assert a.tf_name == "web_server"
    assert b.tf_name == "api_server"
