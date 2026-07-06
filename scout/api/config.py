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
    stripe_unlimited_price_id: str = ""
    stripe_success_url: str = ""
    stripe_cancel_url: str = ""
    stripe_beta_success_url: str = ""
    stripe_beta_cancel_url: str = ""
    stripe_portal_return_url: str = ""
    hosted_key_delivery_smtp_host: str = ""
    hosted_key_delivery_smtp_port: int = 587
    hosted_key_delivery_smtp_from_email: str = ""
    hosted_key_delivery_smtp_username: str = ""
    hosted_key_delivery_smtp_password: str = ""
    hosted_key_delivery_smtp_use_tls: bool = True
    hosted_rate_limit_max_requests: int = 60
    hosted_rate_limit_window_seconds: int = 60
    hosted_beta_signup_rate_limit_max_requests: int = 3
    hosted_beta_signup_rate_limit_window_seconds: int = 3600
    hosted_max_active_requests: int = 8
    hosted_job_queue_max_size: int = 250
    hosted_job_queue_workers: int = 2
    hosted_async_first: bool = False
    playground_max_active_requests: int = 4
    capacity_retry_after_seconds: int = 5
    hosted_beta_signup_enabled: bool = True
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

    # Ignore unknown env vars so an unrelated key in a shared .env (e.g. RESEND_API_KEY)
    # can never crash Scout on startup. Only Scout's declared settings are read.
    model_config = {
        "env_file": (".env", ".env.local"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
