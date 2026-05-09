from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

from jinja2 import Environment, FileSystemLoader


class _InstanceType(NamedTuple):
    cpu: int
    memory_gb: int
    name: str


_INSTANCE_CATALOG: list[_InstanceType] = [
    _InstanceType(1, 1, "t3.micro"),
    _InstanceType(1, 2, "t3.small"),
    _InstanceType(2, 4, "t3.medium"),
    _InstanceType(2, 8, "t3.large"),
    _InstanceType(4, 8, "m5.xlarge"),
    _InstanceType(4, 16, "t3.xlarge"),
    _InstanceType(8, 16, "m5.2xlarge"),
    _InstanceType(8, 32, "t3.2xlarge"),
    _InstanceType(16, 32, "m5.4xlarge"),
    _InstanceType(32, 64, "m5.8xlarge"),
]

_templates = Environment(
    loader=FileSystemLoader(Path(__file__).parent), keep_trailing_newline=True
)


@dataclass
class AwsInstance:
    name: str = field(repr=False)
    cpu: int = field(repr=False)
    memory_gb: int = field(repr=False)
    ami_ref: str
    tf_name: str = field(init=False)
    instance_type: str = field(init=False)

    def __post_init__(self) -> None:
        self.tf_name = self.name.replace("-", "_").replace(" ", "_")
        self.instance_type = self._select_instance(self.cpu, self.memory_gb)

    @staticmethod
    def _select_instance(cpu: int, memory_gb: int) -> str:
        instances = [
            i for i in _INSTANCE_CATALOG if i.cpu >= cpu and i.memory_gb >= memory_gb
        ]
        if not instances:
            raise ValueError(
                f"no instance type found for cpu={cpu}, memory_gb={memory_gb}"
            )
        return min(instances, key=lambda i: (i.cpu, i.memory_gb)).name

    def render(self) -> str:
        return str(
            _templates.get_template("aws_instance.tf.j2").render(
                tf_name=self.tf_name,
                instance_type=self.instance_type,
                ami_ref=f"data.aws_ami.{self.ami_ref}.id",
            )
        )
