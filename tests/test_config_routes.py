"""Tests for provider configuration routes."""

import yaml


def test_provider_config_update_is_rejected_when_locked(client, monkeypatch):
    monkeypatch.setenv('PROVIDER_CONFIG_LOCKED', 'true')

    response = client.post('/api/config', json={
        'text_generation': {
            'active_provider': 'yunwu_text',
            'providers': {}
        }
    })

    assert response.status_code == 403
    assert response.get_json() == {
        'success': False,
        'error': '生产环境已锁定模型配置，请通过部署配置更新'
    }


def test_provider_config_lock_accepts_common_truthy_values(monkeypatch):
    from backend.routes.config_routes import _provider_config_locked

    for value in ('1', 'true', 'TRUE', 'yes', 'on'):
        monkeypatch.setenv('PROVIDER_CONFIG_LOCKED', value)
        assert _provider_config_locked() is True

    monkeypatch.setenv('PROVIDER_CONFIG_LOCKED', 'false')
    assert _provider_config_locked() is False


def test_provider_connection_loads_api_key_from_environment(tmp_path, monkeypatch):
    from backend.routes import config_routes

    config_path = tmp_path / 'text_providers.yaml'
    config_path.write_text(yaml.safe_dump({
        'providers': {
            'tokensfactory': {
                'api_key_env': 'TOKENSFACTORY_API_KEY',
                'base_url': 'https://tokensfactory.cc/v1',
                'model': 'gemini-3.5-flash'
            }
        }
    }), encoding='utf-8')
    monkeypatch.setattr(config_routes, 'TEXT_CONFIG_PATH', config_path)
    monkeypatch.setenv('TOKENSFACTORY_API_KEY', 'test-secret')

    loaded = config_routes._load_provider_config(
        'openai_compatible',
        'tokensfactory',
        {'api_key': None, 'base_url': None, 'model': None}
    )

    assert loaded == {
        'api_key': 'test-secret',
        'base_url': 'https://tokensfactory.cc/v1',
        'model': 'gemini-3.5-flash'
    }
