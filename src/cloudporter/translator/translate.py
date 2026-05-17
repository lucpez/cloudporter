import importlib
from pathlib import Path

from cloudporter.manifest.schema import Manifest


def translate(manifest: Manifest, output_dir: Path, provider: str) -> dict[str, str]:
    try:
        provider_module = importlib.import_module(f"cloudporter.translator.{provider}")
    except ImportError:
        raise ValueError(f"unsupported provider: {provider}") from None
    tofu_files: dict[str, str] = provider_module.render_tofu(manifest)

    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in tofu_files.items():
        (output_dir / filename).write_text(content)

    return tofu_files
