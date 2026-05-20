from pathlib import Path

from scout.api.config import Settings


def test_settings_loads_env_local_after_env(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env_local = tmp_path / ".env.local"
    env.write_text("SCOUT_API_KEY=from-env\nSCOUT_WORKDIR=from-env-workdir\n")
    env_local.write_text("SCOUT_API_KEY=from-env-local\nSCOUT_WORKDIR=from-env-local-workdir\n")

    settings = Settings(_env_file=(env, env_local))

    assert settings.scout_api_key == "from-env-local"
    assert settings.scout_workdir == "from-env-local-workdir"
