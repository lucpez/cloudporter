import warnings
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from cloudporter.manifest.schema import ComputeResource, DatabaseResource, Manifest
from cloudporter.translator.aws.aws_ami import AwsAmi
from cloudporter.translator.aws.aws_db_instance import AwsDbInstance
from cloudporter.translator.aws.aws_instance import AwsInstance
from cloudporter.translator.aws.aws_security_group import AwsSecurityGroup
from cloudporter.translator.references import resolve

_env = Environment(
    loader=FileSystemLoader(Path(__file__).parent), keep_trailing_newline=True
)


def _render_versions() -> str:
    return str(_env.get_template("versions.tf.j2").render())


def _render_variables() -> str:
    return str(_env.get_template("variables.tf.j2").render())


def _render_main(manifest: Manifest) -> str:
    blocks: list[str] = []

    sg = AwsSecurityGroup(manifest.name)
    blocks.append(sg.render())

    for resource in manifest.resources:
        if isinstance(resource, ComputeResource):
            instance_tf_name = resource.name.replace("-", "_").replace(" ", "_")
            ami = AwsAmi(resource.os, instance_tf_name)
            run = resolve(resource.run, manifest, "aws") if resource.run else None
            instance = AwsInstance(
                resource.name,
                resource.cpu,
                resource.memory_gb,
                ami.tf_name,
                sg_tf_name=sg.tf_name,
                public=resource.public,
                run=run,
            )
            blocks.append(ami.render())
            blocks.append(instance.render())
        elif isinstance(resource, DatabaseResource):
            db = AwsDbInstance(
                resource.name,
                resource.engine,
                resource.cpu,
                resource.memory_gb,
                resource.storage_gb,
                sg_tf_name=sg.tf_name,
            )
            blocks.append(db.render())
        else:
            warnings.warn(f"unsupported resource type: {resource.type!r}", stacklevel=2)

    return "\n".join(blocks)


def render_tofu(manifest: Manifest) -> dict[str, str]:
    files: dict[str, str] = {
        "versions.tf": _render_versions(),
        "main.tf": _render_main(manifest),
    }
    has_db = any(isinstance(r, DatabaseResource) for r in manifest.resources)
    if has_db:
        files["variables.tf"] = _render_variables()
    return files


def resource_mapping(manifest: Manifest) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for resource in manifest.resources:
        if isinstance(resource, ComputeResource):
            instance_tf_name = resource.name.replace("-", "_").replace(" ", "_")
            ami = AwsAmi(resource.os, instance_tf_name)
            instance = AwsInstance(
                resource.name,
                resource.cpu,
                resource.memory_gb,
                ami.tf_name,
                sg_tf_name="",
            )
            result.append(
                {
                    "name": resource.name,
                    "type": resource.type,
                    "identifier": instance.instance_type,
                    "variant": "windows" if "windows" in resource.os else "linux",
                }
            )
        elif isinstance(resource, DatabaseResource):
            db = AwsDbInstance(
                resource.name,
                resource.engine,
                resource.cpu,
                resource.memory_gb,
                resource.storage_gb,
            )
            result.append(
                {
                    "name": resource.name,
                    "type": resource.type,
                    "identifier": db.instance_class,
                    "variant": resource.engine,
                }
            )
    return result
