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

- **Orchestrator** (`translate.py`) — provider-agnostic entry point. Exposes two public functions: `translate(manifest, output_dir, provider)` writes OpenTofu files to disk; `mapping(manifest, provider)` returns the provider-specific resource mapping as a list of dicts (`name`, `type`, `identifier`, `variant`) for use by external modules (e.g. cost estimation). Both dynamically load the target provider module. It knows nothing about specific resources or clouds.
- **Provider** (`<provider>/__init__.py`) — exposes two functions: `render_tofu(manifest) -> dict[str, str]` (filenames → HCL content) and `resource_mapping(manifest) -> list[dict[str, str]]` (normalized mapping for `translate.mapping`). Iterates resources, resolves cross-resource dependencies, and delegates each supported type to its resource module.
- **Resource** (`<provider>/<tf_resource>/`) — a dataclass that receives only the values it needs from the provider (already resolved), exposes `render() -> str`, and returns rendered HCL via a co-located Jinja2 template. Provider-specific equivalences (e.g. cpu+memory → instance type) are resolved in `__post_init__`. Resource classes have one job: render HCL. They do not expose pricing or mapping data.

## Conventions

- **Naming** — resource directories and classes follow the Terraform resource name: `aws_instance`, `aws_ami`, `azurerm_virtual_machine`
- **Co-location** — each resource class lives alongside its `.tf.j2` template in the same directory
- **Unknown types** — an unrecognised resource type at the provider dispatch level produces a warning, never a silent skip or an exception. Invalid values within a known resource type raise `ValueError`
- **Closed union** — the manifest schema (`manifest/schema.py`) is the authoritative list of resource types. Adding a new resource type requires updating the schema, not just the translator
- **mapping contract** — `resource_mapping()` must return dicts with exactly these keys: `name` (resource name), `type` (manifest type), `identifier` (provider-specific pricing ID, e.g. `t3.medium`), `variant` (pricing variant, e.g. `linux`, `windows`, `mysql`). Adding a new resource type = add its case to `resource_mapping()` in each provider
