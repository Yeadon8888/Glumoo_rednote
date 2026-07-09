"""Provider configuration helpers."""
import os
from typing import Any, Dict, Iterable, List


def _normalize_env_names(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [name.strip() for name in value.split(",") if name.strip()]
    if isinstance(value, Iterable):
        return [str(name).strip() for name in value if str(name).strip()]
    return []


def resolve_api_key(provider_config: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of provider_config with api_key resolved from env when needed."""
    resolved = provider_config.copy()
    if resolved.get("api_key"):
        return resolved

    env_names = _normalize_env_names(resolved.get("api_key_env"))
    env_names.extend(["GOOGLE_API_KEY", "GEMINI_API_KEY"])

    seen = set()
    for env_name in env_names:
        if env_name in seen:
            continue
        seen.add(env_name)
        api_key = os.getenv(env_name)
        if api_key:
            resolved["api_key"] = api_key
            return resolved

    return resolved
