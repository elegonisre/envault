"""Template rendering: substitute decrypted vault values into a template file."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from envault.vault import decrypt_file

# Matches ${VAR_NAME} or $VAR_NAME placeholders
_PLACEHOLDER_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class RenderResult:
    output: str
    missing_keys: list[str] = field(default_factory=list)
    substituted: int = 0


def _parse_env(text: str) -> dict[str, str]:
    """Parse decrypted .env text into a key/value mapping."""
    env: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip().strip('"\'')
        if key:
            env[key] = value
    return env


def render_template(
    template_path: str | Path,
    vault_path: str | Path,
    password: str,
    output_path: Optional[str | Path] = None,
    strict: bool = False,
) -> RenderResult:
    """Render *template_path* by substituting variables from *vault_path*.

    Args:
        template_path: Path to the template file containing ``${VAR}`` placeholders.
        vault_path: Path to an encrypted ``.env.vault`` file.
        password: Password used to decrypt the vault.
        output_path: If provided, write rendered output to this path.
        strict: If *True*, raise ``KeyError`` when a placeholder has no matching key.

    Returns:
        A :class:`RenderResult` with the rendered text and metadata.
    """
    template_path = Path(template_path)
    vault_path = Path(vault_path)

    decrypted_text = decrypt_file(vault_path, password)
    env = _parse_env(decrypted_text)

    missing: list[str] = []
    substituted = 0

    template = template_path.read_text(encoding="utf-8")

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        nonlocal substituted
        key = match.group(1) or match.group(2)
        if key in env:
            substituted += 1
            return env[key]
        missing.append(key)
        if strict:
            raise KeyError(f"Template variable '{key}' not found in vault")
        return match.group(0)  # leave placeholder unchanged

    rendered = _PLACEHOLDER_RE.sub(_replace, template)

    if output_path is not None:
        Path(output_path).write_text(rendered, encoding="utf-8")

    return RenderResult(output=rendered, missing_keys=missing, substituted=substituted)
