from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    service_name: str = "agenttrace-ai"
    summary_model: str = "gpt-4o-mini"
    openai_api_key: str | None = None
    openai_api_base: str | None = None


def get_settings() -> Settings:
    env_values = _load_dotenv(Path(".env"))
    return Settings(
        service_name=_get_env("AGENTTRACE_SERVICE_NAME", env_values, "agenttrace-ai"),
        summary_model=_get_env("AGENTTRACE_SUMMARY_MODEL", env_values, "gpt-4o-mini"),
        openai_api_key=_get_env("OPENAI_API_KEY", env_values),
        openai_api_base=(
            _get_env("OPENAI_API_BASE", env_values)
            or _get_env("OPENAI_BASE_URL", env_values)
        ),
    )


def _get_env(
    key: str,
    env_values: dict[str, str],
    default: str | None = None,
) -> str | None:
    return os.getenv(key) or env_values.get(key) or default


def _load_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value

    return values
