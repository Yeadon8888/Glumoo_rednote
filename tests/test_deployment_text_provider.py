"""Deployment text provider configuration tests."""

from pathlib import Path

import yaml


def test_cpa_is_the_active_deployment_text_provider():
    config_path = Path(__file__).parents[1] / "docker" / "text_providers.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert config["active_provider"] == "cpa"
    provider = config["providers"]["cpa"]
    assert provider["base_url"] == (
        "https://cliproxyapi-production-2dde.up.railway.app/v1"
    )
    assert provider["model"] == "gpt-5.4-mini"
    assert provider["endpoint_type"] == "/v1/chat/completions"


def test_cpa_text_api_key_is_loaded_only_from_the_environment():
    config_path = Path(__file__).parents[1] / "docker" / "text_providers.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    provider = config["providers"]["cpa"]

    assert provider["api_key_env"] == "CPA_API_KEY"
    assert "api_key" not in provider
