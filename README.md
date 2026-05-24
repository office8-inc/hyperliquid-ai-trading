# Hyperliquid AI Trading

Freqtrade + Hyperliquid を使い、自宅ミニPCで 24H 稼働させる暗号資産トレードBotの運用リポジトリです。

## 方針

- `freqtrade/freqtrade` 本体はフォークしない。
- 公式Dockerイメージを使う。
- GitHubには設定テンプレート、戦略、手順書だけを置く。
- 秘密鍵、取引DB、ログ、学習済みモデル、バックテスト結果はGit管理しない。
- 最初は必ず `dry_run: true` で運用する。
- AIは直接発注しない。AIは補助シグナルを出し、Freqtrade戦略とリスク管理を通す。
- APIサーバー/Web UIはデフォルト無効。使う場合は、ミニPC側で強い認証情報に変更してから有効化する。

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
```

## 初回セットアップ

```bash
git clone git@github.com:office8-inc/hyperliquid-ai-trading.git /opt/hyperliquid-ai-trading
cd /opt/hyperliquid-ai-trading/freqtrade

cp user_data/config-private.example.json user_data/config-private.json
```

`user_data/config-private.json` に、Hyperliquidの `walletAddress` と API wallet の `privateKey` を入れます。

## 起動

```bash
cd /opt/hyperliquid-ai-trading/freqtrade

docker compose pull
docker compose up -d
docker compose ps
docker compose logs -f --tail=200 freqtrade
```

## よく使うコマンド

```bash
# ペア確認
docker compose run --rm freqtrade list-pairs \
  --exchange hyperliquid \
  --trading-mode futures \
  --quote USDC \
  --print-list

# データ取得
docker compose run --rm freqtrade download-data \
  --config /freqtrade/user_data/config.json \
  --config /freqtrade/user_data/config-private.json \
  --trading-mode futures \
  --pairs BTC/USDC:USDC ETH/USDC:USDC \
  --timeframes 5m 15m 1h

# バックテスト
docker compose run --rm freqtrade backtesting \
  --config /freqtrade/user_data/config.json \
  --config /freqtrade/user_data/config-private.json \
  --strategy HLAiMvpStrategy
```

## 実資金に進む条件

- 2週間以上、ミニPCで `dry_run` が安定稼働している。
- 停止、再起動、復旧手順を確認済み。
- エラー通知を受け取れる。
- 1日の最大損失額を決めている。
- 初回資金は失ってもよい小額に限定している。
- API walletを使い、本ウォレットの秘密鍵をBotに置いていない。

## 参照

- Freqtrade: https://github.com/freqtrade/freqtrade
- Freqtrade Docs: https://www.freqtrade.io
- Docker Quickstart: https://www.freqtrade.io/en/stable/docker_quickstart/
- Exchange Notes: https://www.freqtrade.io/en/stable/exchanges/
