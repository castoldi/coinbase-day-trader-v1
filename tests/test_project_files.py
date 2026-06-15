from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_secret_files_are_ignored():
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in ignore
    assert "!.env.example" in ignore
    assert "logs/*" in ignore


def test_required_public_docs_exist():
    for name in ["README.md", "CHANGELOG.md", "AGENTS.md", "VERSION", ".env.example"]:
        assert (ROOT / name).exists(), f"{name} should exist"


def test_env_example_has_no_secret_values():
    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "COINBASE_API_KEY_NAME=" in env_example
    assert "GMAIL_APP_PASSWORD=" in env_example
    assert "replace-me" not in env_example.lower()
