# Hyperliquid AI Trading

Freqtrade + Hyperliquid を使い、自宅ミニPCで 24H 稼働させる暗号資産トレードBotの運用リポジトリです。

## 現在の到達点

このリポジトリは、完成済みの収益Botではありません。
現時点では、FreqtradeをHyperliquid向けに安全に検証し始めるための運用雛形です。

できること:

- Freqtrade公式DockerイメージでBotを起動する準備
- WSL2 Ubuntu上でDockerなしにBotを起動する準備
- Hyperliquid futures向けの設定テンプレート管理
- dry_runを前提にした最小戦略の配置
- 自宅ミニPC運用の手順管理

まだできていないこと:

- 実資金で勝てる戦略の確立
- Hyperliquidでの長期バックテスト
- AIシグナル生成スクリプトの実装
- 常駐PC上での実起動検証
- ライブ運用の監視・通知・バックアップの完成

## 方針

- `freqtrade/freqtrade` 本体はフォークしない。
- Docker構成では公式Dockerイメージを使う。
- Dockerなし構成では、WSL2 Ubuntu上の `/opt/freqtrade` に公式リポジトリをcloneして使う。
- GitHubには設定テンプレート、戦略、手順書だけを置く。
- 秘密鍵、取引DB、ログ、学習済みモデル、バックテスト結果はGit管理しない。
- 最初は必ず `dry_run: true` で運用する。
- AIは直接発注しない。AIは補助シグナルを出し、Freqtrade戦略とリスク管理を通す。
- APIサーバー/Web UIはデフォルト無効。使う場合は、ミニPC側で強い認証情報に変更してから有効化する。
- Hyperliquidでは、Bot専用のsubaccount/API walletを使い、Bot稼働中に同じ口座で手動売買しない。

## 安全性確認メモ

2026-05-24 時点で確認した内容:

- `freqtrade/freqtrade` は公式公開リポジトリで、非アーカイブ、非フォーク。
- 最新リリースは `2026.4`。
- GitHub公開Repository Security Advisoryは空。
- スター数、フォーク数、更新頻度から見て利用実績と保守継続性がある。

ただし、これは「完全に安全」という意味ではありません。実資金投入前に、必ずバックテスト、dry_run、小額ライブの順番で検証します。

## 構成

```text
GitHub
  - コード管理
  - 設定テンプレート
  - 手順書

Windows PC
  - 開発
  - ドキュメント編集
  - 短時間検証

自宅ミニPC
  - Ubuntu Server
  - Docker Compose
  - Freqtrade 24H稼働
  - Hyperliquid dry_run / small live

既存crow-bot常駐PC
  - Windows 10 + WSL2 Ubuntu
  - Dockerなし native Freqtrade
  - systemdでFreqtrade 24H稼働
  - 既存Slack WebSocket / Cloudflare Tunnelとは分離
```

## Freqtradeでできることをこのプロジェクトから使う

このプロジェクトは、Freqtrade本体をコピーしません。
Docker構成では公式Dockerイメージを、Dockerなし構成ではWSL2 Ubuntu上の `/opt/freqtrade/.venv/bin/freqtrade` をラップして使います。
そのため、`freqtrade/freqtrade` のCLIコマンドは、このリポジトリの `scripts/` から呼び出せます。

Docker構成:

```bash
# 任意のFreqtradeコマンドをそのまま呼ぶ
./scripts/ft.sh --help
./scripts/ft.sh list-exchanges

# このプロジェクトのconfig.json + config-private.jsonを付けて呼ぶ
./scripts/ftc.sh show-config
./scripts/ftc.sh list-pairs --exchange hyperliquid --trading-mode futures --quote USDC --print-list
./scripts/ftc.sh backtesting --strategy HLAiMvpStrategy

# plot用イメージで呼ぶ
./scripts/ft-plot.sh plot-profit

# FreqAI用イメージで呼ぶ
./scripts/ft-freqai.sh list-freqaimodels
```

PowerShellでは以下を使います。

```powershell
.\scripts\ft.ps1 --help
.\scripts\ftc.ps1 show-config
.\scripts\ft-plot.ps1 plot-profit
.\scripts\ft-freqai.ps1 list-freqaimodels
```

WSL native構成:

```bash
./scripts/ft-native.sh --help
./scripts/ftc-native.sh show-config
./scripts/ftc-native.sh list-pairs --exchange hyperliquid --trading-mode futures --quote USDC --print-list
```

詳しくは [docs/freqtrade-capabilities.md](docs/freqtrade-capabilities.md) を参照。

常駐ミニPCでDockerを使う場合は [docs/mini-pc-setup.md](docs/mini-pc-setup.md) を参照。
既存crow-bot機でDockerなしのWSL構成を使う場合は [docs/native-wsl-setup.md](docs/native-wsl-setup.md) を参照。

## Docker構成の初回セットアップ

```bash
git clone git@github.com:office8-inc/hyperliquid-ai-trading.git /opt/hyperliquid-ai-trading
cd /opt/hyperliquid-ai-trading

cp freqtrade/user_data/config-private.example.json freqtrade/user_data/config-private.json
```

`freqtrade/user_data/config-private.json` に、Hyperliquidの `walletAddress` と API wallet の `privateKey` を入れます。
`freqtrade/.env` は任意です。FreqtradeのDockerイメージを切り替える場合だけ、ミニPC上で `FREQTRADE_IMAGE=freqtradeorg/freqtrade:2026.4_freqai` のように設定します。

WSL native構成では、[docs/native-wsl-setup.md](docs/native-wsl-setup.md) のユーザー分離、`/opt/freqtrade` インストール、systemd設定を使います。

## Docker構成の起動

```bash
cd /opt/hyperliquid-ai-trading/freqtrade

docker compose pull
docker compose up -d
docker compose ps
docker compose logs -f --tail=200 freqtrade
```

## Docker構成でよく使うコマンド

```bash
cd /opt/hyperliquid-ai-trading

# ペア確認
./scripts/ftc.sh list-pairs --exchange hyperliquid --trading-mode futures --quote USDC --print-list

# データ取得（Hyperliquidでは過去データ取得に強い制限があるため、ベストエフォート扱い）
./scripts/ftc.sh download-data --trading-mode futures --pairs BTC/USDC:USDC ETH/USDC:USDC --timeframes 5m 15m 1h

# バックテスト
./scripts/ftc.sh backtesting --strategy HLAiMvpStrategy
```

## 実資金に進む条件

- 2週間以上、ミニPCで `dry_run` が安定稼働している。
- 停止、再起動、復旧手順を確認済み。
- エラー通知を受け取れる。
- 1日の最大損失額を決めている。
- 初回資金は失ってもよい小額に限定している。
- API walletを使い、本ウォレットの秘密鍵をBotに置いていない。
- Bot専用subaccountで、手動売買と混在していない。

## Hyperliquidの重要な制約

Freqtrade公式ドキュメント上、Hyperliquidはfuturesのみ実用対象で、spotは未対応です。
また、Hyperliquidは過去ローソク足の取得に強い制限があり、長期バックテストを前提にした開発には向きません。

そのため、このプロジェクトの検証順序は以下にします。

```text
短期/限定データで戦略の動作確認
↓
ミニPCでdry_runを長めに回して実データを蓄積
↓
蓄積データで検証
↓
小額ライブ
```

## 参照

- Freqtrade: https://github.com/freqtrade/freqtrade
- Freqtrade Docs: https://www.freqtrade.io
- Docker Quickstart: https://www.freqtrade.io/en/stable/docker_quickstart/
- Exchange Notes: https://www.freqtrade.io/en/stable/exchanges/
