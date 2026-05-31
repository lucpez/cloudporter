from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

from jinja2 import Environment, FileSystemLoader

_MYSQL_VERSION = "8.0"
_POSTGRES_VERSION = "15"

_ENGINE_VERSIONS: dict[str, str] = {
    "mysql": _MYSQL_VERSION,
    "postgres": _POSTGRES_VERSION,
}


class _DbInstanceClass(NamedTuple):
    cpu: int
    memory_gb: int
    name: str


_INSTANCE_CATALOG: list[_DbInstanceClass] = [
    _DbInstanceClass(2, 1, "db.t3.micro"),
    _DbInstanceClass(2, 2, "db.t3.small"),
    _DbInstanceClass(2, 4, "db.t3.medium"),
    _DbInstanceClass(2, 8, "db.t3.large"),
    _DbInstanceClass(4, 16, "db.t3.xlarge"),
    _DbInstanceClass(8, 32, "db.t3.2xlarge"),
    _DbInstanceClass(4, 16, "db.m5.xlarge"),
    _DbInstanceClass(8, 32, "db.m5.2xlarge"),
    _DbInstanceClass(16, 64, "db.m5.4xlarge"),
]

_templates = Environment(
    loader=FileSystemLoader(Path(__file__).parent), keep_trailing_newline=True
)


def select_instance_class(cpu: int, memory_gb: int) -> str:
    matched = [
        i for i in _INSTANCE_CATALOG if i.cpu >= cpu and i.memory_gb >= memory_gb
    ]
    if not matched:
        raise ValueError(
            f"no RDS instance class found for cpu={cpu}, memory_gb={memory_gb}"
        )
    return min(matched, key=lambda i: (i.cpu, i.memory_gb)).name


@dataclass
class AwsDbInstance:
    name: str
    engine: str
    cpu: int
    memory_gb: int
    storage_gb: int
    sg_tf_name: str = ""
    tf_name: str = field(init=False)
    instance_class: str = field(init=False)
    engine_version: str = field(init=False)

    def __post_init__(self) -> None:
        self.tf_name = self.name.replace("-", "_").replace(" ", "_")
        self.instance_class = select_instance_class(self.cpu, self.memory_gb)
        self.engine_version = _ENGINE_VERSIONS[self.engine]

    def render(self) -> str:
        return str(
            _templates.get_template("aws_db_instance.tf.j2").render(
                tf_name=self.tf_name,
                db_name=self.name,
                engine=self.engine,
                engine_version=self.engine_version,
                instance_class=self.instance_class,
                storage_gb=self.storage_gb,
                sg_tf_name=self.sg_tf_name,
            )
        )
