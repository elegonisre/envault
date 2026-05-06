"""Export decrypted vault contents to various formats."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Literal

from envault.vault import decrypt_file

ExportFormat = Literal["dotenv", "json", "shell"]


def _parse_env(content: str) -> Dict[str, str]:
    """Parse decrypted .env content into key/value pairs."""
    pairs: Dict[str, str] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            pairs[key] = value
    return pairs


def export_vault(
    vault_path: str | Path,
    password: str,
    fmt: ExportFormat = "dotenv",
    output_path: str | Path | None = None,
) -> str:
    """Decrypt *vault_path* and render its contents in *fmt* format.

    Returns the rendered string and optionally writes it to *output_path*.
    """
    vault_path = Path(vault_path)
    decrypted = decrypt_file(vault_path, password)
    pairs = _parse_env(decrypted)

    if fmt == "dotenv":
        rendered = "\n".join(f'{k}="{v}"' for k, v in pairs.items()) + "\n"
    elif fmt == "json":
        rendered = json.dumps(pairs, indent=2) + "\n"
    elif fmt == "shell":
        rendered = "\n".join(f"export {k}='{v}'" for k, v in pairs.items()) + "\n"
    else:
        raise ValueError(f"Unknown export format: {fmt!r}")

    if output_path is not None:
        Path(output_path).write_text(rendered)

    return rendered
