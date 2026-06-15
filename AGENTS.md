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

## Strategies

Available strategy names (the registry keys in `src/trader_app/strategies/registry.py`):

| Name | File | Description |
| --- | --- | --- |
| `ema_ribbon_reversal` | `src/trader_app/strategies/ema_ribbon_reversal.py` | EMA ribbon reversal (EMA 5/100/200 of high/low/close, 2:1 reward:risk), encoded from YouTube video `HkMXGqz7MRI`. This is the default strategy. |
| `stochastic_swing` | `src/trader_app/strategies/stochastic_swing.py` | Long-only fast-Stochastic swing: buy when %K(5) < 5 (oversold), take a fixed % profit (default 3%) with a trailing highest-high(5) exit. Encoded from YouTube video `vzgRhKBMSyE`. |
| `triple_screen_trend` | `src/trader_app/strategies/triple_screen_trend.py` | Long-only trend-continuation: buy pullbacks in an EMA 27/55 uptrend confirmed by MACD; swing-low stop, 3:1 target. Adapted from the Renko triple-screen approach in YouTube video `O3Q1uxBaIc0`. |

### Starting the bot with a chosen strategy

The `--strategies` option accepts a single name, a comma-separated list, or `ALL`.

- Start with the EMA ribbon reversal strategy (recommended/default):

  ```powershell
  powershell -File scripts/start_bot.ps1 -Strategies ema_ribbon_reversal
  # or directly:
  trader start-bot --strategies ema_ribbon_reversal
  ```

- Start with every registered strategy:

  ```powershell
  powershell -File scripts/start_bot.ps1 -Strategies ALL
  ```

- Start with several specific strategies (comma-separated, no spaces):

  ```powershell
  trader start-bot --strategies ema_ribbon_reversal,stochastic_swing
  ```

`DEFAULT_STRATEGIES` in `.env` sets the default when `--strategies` is omitted; it is currently `ema_ribbon_reversal`. Each `start-bot` call ensures the heartbeat and runs one paper-trading cycle, so schedule it every ~30 minutes (Windows Task Scheduler).

### Strategy notes

- The transcript was retrieved with the `youtube-transcript-api` Python library: `YouTubeTranscriptApi().fetch("HkMXGqz7MRI")`. Use it to re-pull or refine the rules.
- Strategy signals carry `entry_price`, `stop_loss`, and `take_profit`; the backtest and live engines size positions as `starting_cash / number_of_products` and exit on stop/target or an opposite signal.
- To add a new strategy, implement the `Strategy` protocol in `src/trader_app/strategies/base.py` and register it in `available_strategies()`; it then becomes selectable via `--strategies <name>`.
