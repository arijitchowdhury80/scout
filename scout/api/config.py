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
    hosted_key_delivery_smtp_host: str = ""
    hosted_key_delivery_smtp_port: int = 587
    hosted_key_delivery_smtp_from_email: str = ""
    hosted_key_delivery_smtp_username: str = ""
    hosted_key_delivery_smtp_password: str = ""
    hosted_key_delivery_smtp_use_tls: bool = True
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
