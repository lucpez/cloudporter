import re

from cloudporter.manifest.schema import ComputeResource, DatabaseResource, Manifest

_REF = re.compile(r"\{\{\s*([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_]+)\s*\}\}")

_COMPUTE_ATTRS: dict[str, dict[str, str]] = {
    "aws": {
        "private_ip": "aws_instance.{tf_name}.private_ip",
    },
    "azure": {
        "private_ip": "azurerm_linux_virtual_machine.{tf_name}.private_ip_address",
    },
}

_DB_ATTRS: dict[str, dict[str, dict[str, str]]] = {
    "aws": {
        "mysql": {"host": "aws_db_instance.{tf_name}.address"},
        "postgres": {"host": "aws_db_instance.{tf_name}.address"},
    },
    "azure": {
        "mysql": {"host": "azurerm_mysql_flexible_server.{tf_name}.fqdn"},
        "postgres": {"host": "azurerm_postgresql_flexible_server.{tf_name}.fqdn"},
    },
}


def resolve(script: str, manifest: Manifest, provider: str) -> str:
    def _replace(m: re.Match[str]) -> str:
        name, attr = m.group(1), m.group(2)
        tf_name = name.replace("-", "_").replace(" ", "_")

        if name == "var":
            return "${var." + attr + "}"

        resource = next((r for r in manifest.resources if r.name == name), None)
        if resource is None:
            raise ValueError(f"reference to unknown resource: {name!r}")

        if isinstance(resource, ComputeResource):
            tmpl = _COMPUTE_ATTRS.get(provider, {}).get(attr)
            if tmpl is None:
                raise ValueError(
                    f"unknown attribute {attr!r} for compute on {provider}"
                )
            return "${" + tmpl.format(tf_name=tf_name) + "}"

        if isinstance(resource, DatabaseResource):
            tmpl = _DB_ATTRS.get(provider, {}).get(resource.engine, {}).get(attr)
            if tmpl is None:
                raise ValueError(
                    f"unknown attribute {attr!r} for "
                    f"database ({resource.engine}) on {provider}"
                )
            return "${" + tmpl.format(tf_name=tf_name) + "}"

        raise ValueError(f"unsupported resource type for reference: {resource.type!r}")

    return _REF.sub(_replace, script)
