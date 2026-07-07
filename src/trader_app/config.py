from enum import StrEnum

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TradingMode(StrEnum):
    PAPER = "paper"
    COINBASE_SANDBOX = "coinbase_sandbox"
    LIVE = "live"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "local"
    database_url: str = "sqlite:///./data/trader.sqlite3"
    trading_mode: TradingMode = Field(default=TradingMode.PAPER, alias="TRADING_MODE")
    bot_starting_cash_usd: float = 1000
    bot_max_drawdown_fraction: float = 0.5
    bot_heartbeat_stale_seconds: int = 1800
    default_products: str = "BTC-USD,ETH-USD,SOL-USD"
    default_strategies: str = "ema_ribbon_reversal"
    # Candle granularity used by the live candle loader. One of the names in
    # trader_app.backtests.granularity.GRANULARITY_SECONDS.
    backtest_granularity: str = "ONE_DAY"
    # Comma-separated granularities the standard backtest sweep compares
    # side-by-side (coin x granularity x period x strategy).
    backtest_granularities: str = "ONE_DAY,ONE_HOUR,FIVE_MINUTE"
    # Per-side trading fee applied on both entry and exit in backtests and
    # paper trading. Coinbase taker fees are commonly up to 0.6%; tune to your
    # current fee tier. At intraday frequencies this dominates results, so do
    # not leave it at zero.
    backtest_fee_rate: float = 0.006
    coinbase_api_key_name: str = ""
    coinbase_api_private_key: str = ""
    coinbase_sandbox_base_url: str = "https://api.coinbase.com"
    gmail_smtp_host: str = "smtp.gmail.com"
    gmail_smtp_port: int = 587
    gmail_user: str = ""
    gmail_app_password: str = ""
    email_to: str = ""
    notify_email: str = ""
    api_host: str = "127.0.0.1"
    api_port: int = 7011
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8011
    email_subject_prefix: str = "AI-BOT"

    @model_validator(mode="after")
    def block_live_mode(self) -> "Settings":
        if self.trading_mode == TradingMode.LIVE:
            raise ValueError("Live trading is not implemented in v0.1.0")
        if not 0 < self.bot_max_drawdown_fraction <= 1:
            raise ValueError("bot_max_drawdown_fraction must be between 0 and 1")
        return self

    @property
    def products(self) -> list[str]:
        return [item.strip() for item in self.default_products.split(",") if item.strip()]
