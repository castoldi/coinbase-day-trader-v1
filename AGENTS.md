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
