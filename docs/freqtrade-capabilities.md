# Freqtrade Capabilities in This Project

This repository does not copy the `freqtrade/freqtrade` source tree.
Instead, it exposes the official Freqtrade Docker image through project-local wrappers.

That means the project can run the Freqtrade CLI commands provided by the selected Docker image while keeping local configuration, strategies, AI signals, logs, and operational docs in this repository.

## Docker images

Default image:

```text
freqtradeorg/freqtrade:2026.4
```

Verified optional image tags:

```text
freqtradeorg/freqtrade:2026.4_plot
freqtradeorg/freqtrade:2026.4_freqai
freqtradeorg/freqtrade:2026.4_freqaitorch
freqtradeorg/freqtrade:2026.4_freqairl
```

Use image variants when the command requires optional dependencies.

## Command wrappers

Run any raw Freqtrade command:

```bash
./scripts/ft.sh --help
./scripts/ft.sh list-exchanges
./scripts/ft.sh create-userdir --userdir user_data
```

Run commands with this project's default config files:

```bash
./scripts/ftc.sh show-config
./scripts/ftc.sh list-pairs --exchange hyperliquid --trading-mode futures --quote USDC --print-list
./scripts/ftc.sh backtesting --strategy HLAiMvpStrategy
```

Run plotting commands:

```bash
./scripts/ft-plot.sh plot-dataframe --strategy HLAiMvpStrategy -p BTC/USDC:USDC
./scripts/ft-plot.sh plot-profit
```

Run FreqAI commands:

```bash
./scripts/ft-freqai.sh list-freqaimodels
./scripts/ft-freqai.sh backtesting --strategy SomeFreqAIStrategy --freqaimodel LightGBMRegressor
```

PowerShell equivalents are available:

```powershell
.\scripts\ft.ps1 --help
.\scripts\ftc.ps1 show-config
.\scripts\ft-plot.ps1 plot-profit
.\scripts\ft-freqai.ps1 list-freqaimodels
```

## Freqtrade command coverage

The wrapper can call the Freqtrade commands available in the Docker image, including:

```text
trade
create-userdir
new-config
show-config
new-strategy
download-data
convert-data
convert-trade-data
trades-to-ohlcv
list-data
backtesting
backtesting-show
backtesting-analysis
edge
hyperopt
hyperopt-list
hyperopt-show
list-exchanges
list-markets
list-pairs
list-strategies
list-hyperoptloss
list-freqaimodels
list-timeframes
show-trades
test-pairlist
convert-db
install-ui
plot-dataframe
plot-profit
webserver
strategy-updater
lookahead-analysis
recursive-analysis
```

## Important limits

- The wrappers expose Freqtrade capabilities, but they do not make a profitable strategy.
- Hyperliquid historical data is limited, so long-term Hyperliquid backtesting is constrained.
- Commands that require optional dependencies may need the `_plot`, `_freqai`, `_freqaitorch`, or `_freqairl` image.
- Live trading still requires manual validation on the mini PC: `docker compose config`, `show-config`, `list-pairs`, `dry_run`, restart tests, and alerts.
- Secrets must stay in ignored files such as `config-private.json`, `config-api.json`, or `config-live.json`.
