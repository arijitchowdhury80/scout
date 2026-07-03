"""Scout API configuration — loads settings from environment or .env file."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings resolved from environment variables or .env file."""

    scout_api_key: str = "dev-key"
    llm_api_key: str = ""
    scout_workdir: str = "scout-runs"
    db_path: str = ""
    hosted_account_db_path: str = ""
    stripe_webhook_secret: str = ""
    stripe_secret_key: str = ""
    stripe_beta_price_id: str = ""
    stripe_standard_1000_price_id: str = ""
    stripe_standard_3000_price_id: str = ""
    stripe_standard_15000_price_id: str = ""
    stripe_browser_100_price_id: str = ""
    stripe_success_url: str = ""
    stripe_cancel_url: str = ""
    hosted_key_delivery_smtp_host: str = ""
    hosted_key_delivery_smtp_port: int = 587
    hosted_key_delivery_smtp_from_email: str = ""
    hosted_key_delivery_smtp_username: str = ""
    hosted_key_delivery_smtp_password: str = ""
    hosted_key_delivery_smtp_use_tls: bool = True
    hosted_rate_limit_max_requests: int = 60
    hosted_rate_limit_window_seconds: int = 60
    hosted_max_active_requests: int = 8
    playground_max_active_requests: int = 4
    capacity_retry_after_seconds: int = 5
    hosted_beta_signup_enabled: bool = False
    hosted_llm_mode: str = "disabled"
    hosted_llm_provider_allowlist: str = ""
    scout_public_hosted_only: bool = False
    host: str = "0.0.0.0"
    port: int = 8421

    def resolve_db_path(self) -> str:
        if self.db_path:
            return self.db_path
        return str(__import__("pathlib").Path(self.scout_workdir) / "scout.db")

    def resolve_hosted_account_db_path(self) -> str:
        if self.hosted_account_db_path:
            return self.hosted_account_db_path
        return str(__import__("pathlib").Path(self.scout_workdir) / "hosted_accounts.sqlite")

    model_config = {"env_file": (".env", ".env.local"), "env_file_encoding": "utf-8"}


settings = Settings()
