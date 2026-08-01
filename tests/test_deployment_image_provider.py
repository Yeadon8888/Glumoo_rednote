"""Deployment image provider configuration tests."""

from pathlib import Path

import yaml


def test_cpa_is_the_active_deployment_image_provider():
    config_path = Path(__file__).parents[1] / "docker" / "image_providers.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert config["active_provider"] == "cpa_gpt_image"
    provider = config["providers"]["cpa_gpt_image"]
    assert provider["base_url"] == (
        "https://cliproxyapi-production-2dde.up.railway.app/v1"
    )
    assert provider["model"] == "gpt-image-2"
    assert provider["endpoint_type"] == "/v1/images/generations"
    assert provider["edit_endpoint"] == "/v1/images/edits"
    assert provider["response_format"] == "b64_json"
    assert provider["max_concurrent"] == 5
    assert provider["min_free_storage_mb"] == 64
    assert provider["output_size"] == "1536x2048"


def test_cpa_api_key_is_loaded_only_from_the_environment():
    config_path = Path(__file__).parents[1] / "docker" / "image_providers.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    provider = config["providers"]["cpa_gpt_image"]

    assert provider["api_key_env"] == "CPA_IMAGE_API_KEY"
    assert "api_key" not in provider
