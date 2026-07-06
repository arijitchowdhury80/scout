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


def test_settings_default_unlimited_price_id_is_empty() -> None:
    settings = Settings(_env_file=())

    assert settings.stripe_unlimited_price_id == ""


def test_settings_reads_unlimited_price_id_from_env(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("STRIPE_UNLIMITED_PRICE_ID=price_unlimited_monthly\n")

    settings = Settings(_env_file=(env,))

    assert settings.stripe_unlimited_price_id == "price_unlimited_monthly"
