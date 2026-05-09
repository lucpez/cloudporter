from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_AMI_CATALOG: dict[str, tuple[str, str]] = {
    "ubuntu-22.04": (
        "099720109477",
        "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*",
    ),
    "ubuntu-24.04": (
        "099720109477",
        "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*",
    ),
    "windows-server-2022": (
        "801119661308",
        "Windows_Server-2022-English-Full-Base-*",
    ),
}

_templates = Environment(
    loader=FileSystemLoader(Path(__file__).parent), keep_trailing_newline=True
)


@dataclass
class AwsAmi:
    os: str = field(repr=False)
    tf_name: str = field(init=False)
    owner: str = field(init=False)
    name_filter: str = field(init=False)

    def __post_init__(self) -> None:
        if self.os not in _AMI_CATALOG:
            raise ValueError(f"unsupported OS: {self.os!r}")
        self.owner, self.name_filter = _AMI_CATALOG[self.os]
        self.tf_name = self.os.replace("-", "_").replace(".", "_")

    def render(self) -> str:
        return str(
            _templates.get_template("aws_ami.tf.j2").render(
                tf_name=self.tf_name, owner=self.owner, name_filter=self.name_filter
            )
        )
