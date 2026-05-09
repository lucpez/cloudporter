import warnings
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from cloudporter.manifest.schema import ComputeResource
from cloudporter.translator.aws.aws_ami import AwsAmi
from cloudporter.translator.aws.aws_instance import AwsInstance

_env = Environment(
    loader=FileSystemLoader(Path(__file__).parent), keep_trailing_newline=True
)


def _render_versions() -> str:
    return str(_env.get_template("versions.tf.j2").render())


def _render_main(resources: list[Any]) -> str:
    amis: dict[str, AwsAmi] = {}
    instances: list[AwsInstance] = []

    for resource in resources:
        if isinstance(resource, ComputeResource):
            ami = AwsAmi(resource.os)
            amis[ami.tf_name] = ami
            instances.append(
                AwsInstance(
                    resource.name, resource.cpu, resource.memory_gb, ami.tf_name
                )
            )
        else:
            warnings.warn(f"unsupported resource type: {resource.type!r}", stacklevel=2)

    blocks: list[str] = []
    for ami in sorted(amis.values(), key=lambda a: a.tf_name):
        blocks.append(ami.render())
    for instance in instances:
        blocks.append(instance.render())

    return "\n".join(blocks)


def render_tofu(resources: list[Any]) -> dict[str, str]:
    return {
        "versions.tf": _render_versions(),
        "main.tf": _render_main(resources),
    }
