---
paths:
  - "src/cloudporter/translator/**"
---

# Translator conventions

Conventions for working in the translator module.

## Layers

```
translator/
├── translate.py
├── <provider>/
│   ├── __init__.py
│   ├── versions.tf.j2
│   ├── <tf_resource>/
│   │   ├── __init__.py
│   │   └── <tf_resource>.tf.j2
│   └── <another_tf_resource>/
│       ├── __init__.py
│       └── <another_tf_resource>.tf.j2
└── <another_provider>/
    ├── __init__.py
    ├── versions.tf.j2
    └── ...
```

- **Orchestrator** (`translate.py`) — provider-agnostic entry point. Dynamically loads the target provider module and writes the output files. It knows nothing about specific resources or clouds.
- **Provider** (`<provider>/__init__.py`) — exposes `render_tofu(resources: list[Any]) -> dict[str, str]`, where keys are output filenames. Iterates the resource list, resolves any cross-resource dependencies where needed, and delegates each supported type to its resource module.
- **Resource** (`<provider>/<tf_resource>/`) — a dataclass that receives only the values it needs from the provider (already resolved), exposes `render() -> str`, and returns rendered HCL via a co-located Jinja2 template. Provider-specific equivalences (e.g. cpu+memory → instance type) are resolved in `__post_init__`.

## Conventions

- **Naming** — resource directories and classes follow the Terraform resource name: `aws_instance`, `aws_ami`, `azurerm_virtual_machine`
- **Co-location** — each resource class lives alongside its `.tf.j2` template in the same directory
- **Unknown types** — an unrecognised resource type at the provider dispatch level produces a warning, never a silent skip or an exception. Invalid values within a known resource type raise `ValueError`
- **Closed union** — the manifest schema (`manifest/schema.py`) is the authoritative list of resource types. Adding a new resource type requires updating the schema, not just the translator
