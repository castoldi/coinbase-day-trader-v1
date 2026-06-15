# Changelog

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
