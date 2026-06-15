# Changelog

## 0.6.0 - 2026-06-15

- Reworked the Backtests page into a per-coin breakdown matrix: one section per coin, rows = periods, columns = strategies (each cell shows return with trades · win rate), plus a per-coin Buy & Hold column — so you can compare strategies coin-by-coin and period-by-period. Replaced the combined all-coins summary.

## 0.5.1 - 2026-06-15

- Added a "Combined — all coins" summary table per strategy on the Backtests page (per period: total trades, trade-weighted win rate, combined equity, return, average Buy & Hold), keeping the per-coin detail below it.

## 0.5.0 - 2026-06-15

- Backtests now run **per coin** (per strategy, per period, per coin), each coin starting with $1000, so you can see how each strategy performed on each coin (BTC/ETH/SOL) in each period instead of a blended portfolio number.
- Added a `product_id` column to backtest runs and a "Coin" column to the Backtests table; the Buy & Hold benchmark is now per coin.

## 0.4.4 - 2026-06-15

- Renamed the Backtests "Market" column to "Buy & Hold" and added a note clarifying it is the market benchmark (identical for every strategy), not the strategy's own result.

## 0.4.3 - 2026-06-15

- The active dashboard page is now kept in the URL hash, so a refresh stays on the same page instead of jumping back to Live Trading.
- Live data now updates via async background polling (every 10s) and on navigation, refreshing in place without a full-page reload.

## 0.4.2 - 2026-06-15

- Fixed stale backtest data caused by cached API responses: the API now sends `Cache-Control: no-store`, the dashboard fetches with `cache: "no-store"`, and the dashboard refetches whenever you switch tabs (so each navigation makes a live request).

## 0.4.1 - 2026-06-15

- Stopped the dev server from letting the browser cache assets (`Cache-Control: no-store`) so a refresh always shows the latest dashboard.
- Added a visible "Build <version>" indicator in the sidebar to confirm which build is loaded.

## 0.4.0 - 2026-06-15

- Added a third strategy, `triple_screen_trend`, adapted from YouTube video `O3Q1uxBaIc0`: long-only trend-continuation on an EMA 27/55 uptrend, MACD momentum filter, pullback entry, swing-low stop, and 3:1 target.
- Fixed the Strategies page so each strategy card shows its own latest backtest result instead of a shared global one.
- Confirmed the Backtests page renders one isolated section per strategy; `run-backtests` records each strategy independently.
- Added the new strategy (with candlestick examples) to the Strategy page and refreshed dashboard screenshots.

## 0.3.1 - 2026-06-15

- Fixed the Backtests page to group runs into a separate section per strategy (with its own periods and results table) instead of mislabeling all runs as one strategy. Added an overall "N runs across M strategies" summary.

## 0.3.0 - 2026-06-15

- Added a second strategy, `stochastic_swing`, encoded from YouTube video `vzgRhKBMSyE`: long-only fast-Stochastic %K(5) oversold entry, fixed % target, and a trailing highest-high(5) exit.
- Added an optional `exit_signal` hook so strategies can drive path-dependent exits; wired it into both the backtest simulator and the live trading engine.
- `run-backtests` now runs every registered strategy, so the Backtests page covers all strategies.
- Added the new strategy (with candlestick examples) to the Strategy page and refreshed the dashboard screenshots.
- Real backtests: `stochastic_swing` shows high win rates (2024 71%, 2025 87%, 2026 80%) with small targets.

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
