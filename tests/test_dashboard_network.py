from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_start_script_binds_to_lan_interface():
    script = (ROOT / "scripts" / "start_dashboard.ps1").read_text(encoding="utf-8")
    assert "--host 0.0.0.0" in script
    assert "--port 8011" in script


def test_vite_config_exposes_dashboard_and_proxies_api():
    config = (ROOT / "dashboard" / "vite.config.ts").read_text(encoding="utf-8")
    assert "host: \"0.0.0.0\"" in config
    assert "port: 8011" in config
    assert "target: \"http://127.0.0.1:8000\"" in config
