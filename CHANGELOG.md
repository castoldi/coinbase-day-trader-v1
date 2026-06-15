# Changelog

## 0.2.2 - 2026-06-15

- Documented the available strategies and how to start the bot with a chosen strategy (`ema_ribbon_reversal`, a list, or `ALL`) in `AGENTS.md`.

## 0.2.1 - 2026-06-15

- Captured fresh dashboard screenshots (Live, Strategies, Backtests) from the running app and embedded them in the README.
- Hardened the Live page against summary payloads without a metrics object.

## 0.2.0 - 2026-06-15

- Implemented the real first strategy, `ema_ribbon_reversal`, encoded faithfully from the source YouTube video transcript (EMA 5/100/200 ribbon reversal with 2:1 reward:risk). Replaced the transcript-gated placeholder.
- Added a backtest simulation engine that executes the strategy bar-by-bar across the 2024/2025/2026/last-30-day periods and records trade count, win rate, ending equity, return, and max drawdown.
- Added a live trading cycle (`TradingEngine`) that loads market data, opens/closes paper trades against the account, and honors the 50% drawdown safety lock; wired into `trader start-bot`.
- Added Gmail email notifications (`AI-BOT` subject prefix) for bot start/restart and trade open/close events.
- Added a `/api/strategies` endpoint plus a Strategy page with candlestick chart examples annotating entry, stop-loss, and take-profit for the long and short setups.
- Added live coin prices and full open/closed trade tables to the dashboard.
- Persisted per-trade stop-loss and take-profit levels.

## 0.1.3 - 2026-06-15

- Fixed dashboard menu buttons so they switch between Live Trading, Trading History, Account Management, Backtests, and Strategies.
- Added visible placeholder content for pages whose backend data is not implemented yet.
- Added Backtests page standard periods: 2024, 2025, 2026, and Last 30 days.
- Added dashboard interaction tests for menu clicks and Backtests page content.

## 0.1.2 - 2026-06-15

- Changed the dashboard development host to `0.0.0.0` so it can be reached from the local network at URLs such as `http://192.168.0.191:8011/`.
- Added Vite `/api` proxying to the local FastAPI backend.
- Added tests that lock the dashboard LAN host, port, and proxy behavior.

## 0.1.1 - 2026-06-15

- Changed the dashboard development port from 5173 to 8011 across settings, `.env.example`, scripts, docs, and dashboard package metadata.
- Updated config tests so local ignored `.env` secrets do not override default-setting assertions.

## 0.1.0 - 2026-06-15

- Added approved local paper trading design.
- Started v0.1.0 implementation plan.
- Established safety-first project metadata and documentation.
- Added typed configuration with live-trading fail-closed behavior.
- Added SQLite paper account, safety lock, strategy registry, paper broker, Coinbase sandbox smoke client, bot heartbeat, standard backtest periods, FastAPI dashboard API, dashboard shell, and rotating logs.
- Added secret-safe ignore rules for `.env`, Coinbase API key exports, runtime databases, logs, caches, and generated package metadata.
- Added the first live trading dashboard screenshot.
