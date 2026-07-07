# Coinbase Day Trader v1

Local-first Coinbase crypto paper trading bot and dashboard.

## Financial Disclaimer

This project is experimental software. The owner is not a financial professional, and this repository does not provide financial advice. Do not use this software for live trading unless you understand the risks and have reviewed the code, configuration, exchange permissions, and strategy behavior yourself.

## Current Safety Mode

Version 0.2.0 supports local paper trading first. Coinbase integration is wired for sandbox/public API checks, but live order placement is intentionally blocked. The bot trades paper money only and stops permanently if equity falls to 50% of the starting balance until you run `trader reset-safety`.

## Quick Start

1. Copy `.env.example` to `.env`.
2. Fill only the values you need for local testing.
3. Install Python dependencies with `pip install -e .[dev]`.
4. Start the bot with `powershell -File scripts/start_bot.ps1 -Strategies ALL`.
5. Start the dashboard with `powershell -File scripts/start_dashboard.ps1`.

## Coinbase Setup

Create Coinbase API credentials from Coinbase Developer Platform or Advanced Trade with the least permissions needed for sandbox and market-data testing. Store keys only in `.env` or another ignored local secret file. Do not commit `.env`, `cdp_api_key.json`, or any API key export.

In v0.1.3, `TRADING_MODE=paper` is the safe default. `TRADING_MODE=coinbase_sandbox` is reserved for integration smoke checks. `TRADING_MODE=live` fails closed.

## Bot Commands

```powershell
trader start-bot --strategies ALL
trader start-bot --strategies price_action_transcript
trader reset-safety
```

The bot starts from 1000 USD paper cash. Paper entries and exits include the simulated per-side trading fee configured by `BACKTEST_FEE_RATE` (default `0.006`, or 0.6%). If equity falls to 500 USD or below, trading is disabled until `trader reset-safety` is run manually.

## Dashboard

Live trading control room with account metrics, current coin prices, and open/closed trade tables:

![Live trading dashboard](screenshots/dashboard-live.png)

Strategy page with annotated candlestick examples (entry, stop-loss, take-profit) for the long and short setups:

![Strategy page](screenshots/dashboard-strategies.png)

Backtests page summarizing every standard period:

![Backtests page](screenshots/dashboard-backtests.png)

Run locally:

```powershell
powershell -File scripts/start_dashboard.ps1
```

The dashboard binds to all local network interfaces and runs on port `8011`. The backend API listens on port `7011`. On this machine, use [http://127.0.0.1:8011](http://127.0.0.1:8011) for the dashboard and [http://127.0.0.1:7011](http://127.0.0.1:7011) for the API. From another device on the same network, use a LAN URL such as [http://192.168.0.191:8011](http://192.168.0.191:8011).

## Strategies

- `ema_ribbon_reversal`: an EMA ribbon reversal price-action strategy encoded from the source YouTube video transcript.
  - **Orange line** — EMA(200) of close for trend direction.
  - **Green channel** — EMA(100) of high and EMA(100) of low for the pullback zone.
  - **White channel** — EMA(5) of high and EMA(5) of low for the end-of-pullback trigger.
  - **Long:** price and white channel cross above the orange line, price pulls back to touch the green channel, then a candle closes above the white channel. Stop below the green channel; take-profit at 2:1 reward:risk. Short is the mirror image (paper trading is long-only spot, so short signals close open longs).
- `stochastic_swing`: a long-only fast-Stochastic swing strategy encoded from a swing-trade video.
  - **Entry:** fast Stochastic %K (period 5) drops below 5 (oversold) — buy at the close.
  - **Exit:** a fixed percentage target above entry (default 3%; smaller targets raise the win rate), with a trailing highest-high(5) line that exits the position if the target is not reached.
- `triple_screen_trend`: a long-only trend-continuation strategy adapted from a Renko triple-screen (Alexander Elder) video.
  - **Entry:** EMA 27 above EMA 55 (uptrend), price pulls back to the moving-average zone, then reclaims the fast EMA with a bullish candle while MACD agrees.
  - **Exit:** stop at the recent swing low; take-profit at 3:1 reward:risk.

The Strategies page in the dashboard shows annotated candlestick chart examples for each strategy's setups.

Select strategies at startup with `--strategies` (a single name, a comma-separated list, or `ALL`); see `AGENTS.md`.

## Backtests

Standard periods are 2024, 2025, 2026, and the last 30 days. Backtests run **per strategy, per period, per coin** (BTC-USD, ETH-USD, SOL-USD) — each coin starts with 1000 USD paper cash — so you can see exactly how each strategy performed on each coin in each period. Every run records trade count, win rate, ending equity, total return, max drawdown, and a per-coin Buy & Hold benchmark. The dashboard presents this as a per-coin matrix (rows = periods, columns = strategies) so you can compare strategies coin-by-coin. Daily market data is downloaded from the Coinbase public API and cached under `data/market/` for reuse.

Run all standard backtests:

```powershell
trader run-backtests
```

## Email Notifications

Set `GMAIL_USER`, `GMAIL_APP_PASSWORD`, and `NOTIFY_EMAIL` in `.env` to receive emails (subject prefixed `AI-BOT`) when the bot starts/restarts and when paper trades open or close. If credentials are absent, notifications are silently skipped.

## Verification

Backend:

```powershell
pytest -v
```

Dashboard:

```powershell
npm --prefix dashboard test -- --run
npm --prefix dashboard audit --audit-level=moderate
```
