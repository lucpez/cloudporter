from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_templates = Environment(
    loader=FileSystemLoader(Path(__file__).parent), keep_trailing_newline=True
)


@dataclass
class AwsSecurityGroup:
    manifest_name: str
    tf_name: str = field(init=False)
    sg_name: str = field(init=False)

    def __post_init__(self) -> None:
        self.tf_name = self.manifest_name.replace("-", "_").replace(" ", "_")
        self.sg_name = self.manifest_name

    def render(self) -> str:
        return str(
            _templates.get_template("aws_security_group.tf.j2").render(
                tf_name=self.tf_name,
                sg_name=self.sg_name,
            )
        )
