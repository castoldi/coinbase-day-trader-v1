# Agent Instructions

## Safety

- Never commit `.env` or secret values.
- Keep live Coinbase trading blocked until a future explicit implementation enables it.
- Treat local paper trading as the default mode.
- Use tests before production code changes.

## Versioning

- Update `VERSION` and `CHANGELOG.md` for meaningful changes.
- Commit focused changes.
- Tags use `vX.Y.Z-YYYYMMDD-HHMMSS-CT`.

## Operations

- Bot logs and dashboard logs live under `logs/`.
- Market data cache lives under `data/`.
- Runtime databases and logs are not committed.
- `trader start-bot --strategies ALL` ensures the heartbeat and runs one paper-trading cycle; schedule it every ~30 minutes.
- `trader run-backtests` runs the standard periods; `trader reset-safety` clears the drawdown lock.

## Strategy

- The active strategy is `ema_ribbon_reversal` in `src/trader_app/strategies/ema_ribbon_reversal.py`, encoded from YouTube video `HkMXGqz7MRI`.
- The transcript was retrieved with the `youtube-transcript-api` Python library: `YouTubeTranscriptApi().fetch("HkMXGqz7MRI")`. Use it to re-pull or refine the rules.
- Strategy signals carry `entry_price`, `stop_loss`, and `take_profit`; the backtest and live engines size positions as `starting_cash / number_of_products` and exit on stop/target or an opposite signal.
