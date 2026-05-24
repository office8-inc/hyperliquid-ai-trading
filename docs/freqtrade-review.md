# Freqtrade Review Notes

Review date: 2026-05-24

## Conclusion

This repository is a starting scaffold, not a finished trading system.
Using `freqtrade/freqtrade` via the official Docker image is a reasonable starting point, but live trading requires additional validation.

## What was checked

- `freqtrade/freqtrade` tag `2026.4` was cloned for source review.
- Official Docker usage pattern was checked against `docker-compose.yml` and `docs/docker_quickstart.md`.
- Multiple config file support was checked in `docs/configuration.md` and `freqtrade/configuration/configuration.py`.
- Hyperliquid support was checked in `docs/exchanges.md`, `docs/includes/exchange-features.md`, and `freqtrade/exchange/hyperliquid.py`.
- Strategy interface requirements were checked in `freqtrade/strategy/interface.py` and strategy documentation.

## Important findings

- Hyperliquid is supported for futures trading in Freqtrade.
- Hyperliquid spot is listed as not supported.
- Hyperliquid supports isolated and cross futures, but this project starts with isolated mode.
- Hyperliquid does not support normal market orders; Freqtrade/ccxt may simulate them. This project uses limit orders by default.
- Hyperliquid supports stoploss on exchange for futures, so the MVP strategy enables it.
- Freqtrade docs recommend Hyperliquid API wallet usage and warn against sharing the account with manual trading while the bot is running.
- Hyperliquid historical candle availability is limited. This project should not rely on long-term Hyperliquid backtests at the beginning.

## Current repository status

Safe enough for:

- Public template repository
- Local setup
- dry_run testing
- Mini PC deployment rehearsal

Not safe enough yet for:

- Meaningful live capital
- High leverage
- Fully automated AI-driven order placement
- Claims of profitability

## Required next validation

1. Install Docker on the mini PC.
2. Run `docker compose config`.
3. Run `show-config` with both public and private config files.
4. Run `list-pairs` against Hyperliquid.
5. Start `dry_run`.
6. Confirm stop/restart/recovery.
7. Add Telegram or another alert channel.
8. Run for at least two weeks before small live trading.
