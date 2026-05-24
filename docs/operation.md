# Operation Manual

## 役割分担

| 環境 | 役割 |
| --- | --- |
| GitHub | コード、設定テンプレート、手順書を管理 |
| Windows PC | 開発、ドキュメント編集、短時間検証 |
| 自宅ミニPC | FreqtradeをDockerで24H稼働 |

## 現在のステータス

このリポジトリは完成済みの収益Botではなく、Freqtrade + Hyperliquid を検証するための初期運用雛形。
実資金投入は、dry_runで安定稼働を確認してから小額で行う。

## Git管理するもの / しないもの

GitHubには、コード、公開可能な設定テンプレート、戦略、手順書だけを置く。

Git管理するもの:

- `docs/`
- `freqtrade/docker-compose.yml`
- `freqtrade/user_data/config.json`
- `freqtrade/user_data/config-*.example.json`
- `freqtrade/user_data/strategies/`
- `freqtrade/user_data/ai_signals/latest.example.json`
- `scripts/`

Git管理しないもの:

- `freqtrade/.env`
- `freqtrade/user_data/config-private.json`
- `freqtrade/user_data/config-api.json`
- `freqtrade/user_data/config-live.json`
- `freqtrade/user_data/data/`
- `freqtrade/user_data/logs/`
- `freqtrade/user_data/models/`
- `freqtrade/user_data/backtest_results/`
- `freqtrade/user_data/hyperopt_results/`
- `freqtrade/user_data/tradesv3.sqlite*`
- `freqtrade/user_data/*.sqlite*`

迷ったら追加前に `.gitignore` と `git status --short` を確認する。秘密鍵、APIキー、取引DB、ログ、モデル成果物はGitHubへ置かない。

## Hyperliquid運用上の注意

- HyperliquidはFreqtrade上ではfutures運用を前提にする。
- spotは未対応。
- 公式ドキュメントでは、過去ローソク足取得に強い制限がある。
- 長期バックテストだけで判断せず、dry_runでデータと運用実績を積む。
- Bot専用subaccount/API walletを使う。
- Bot稼働中に同じ口座で手動売買しない。

## ミニPC初期セットアップ

1. Ubuntu Server系Linuxを入れる。
2. 有線LANで接続する。
3. スリープを無効化する。
4. BIOSで停電復帰時の自動起動を有効化する。
5. SSHはLANまたはVPN経由だけにする。
6. Docker Engine、Docker Compose Plugin、Gitを入れる。

## ミニPC要件

最低ライン:

- CPU: Intel N100相当以上。
- メモリ: 8GB以上。
- SSD: 128GB以上。
- ネットワーク: 有線LAN。
- OS: Ubuntu Server系Linux。

推奨ライン:

- メモリ: 16GB以上。
- SSD: 256GB以上。
- 小型UPSを接続する。
- BIOSで停電復帰後の自動起動を有効化する。
- 冷却と設置場所を安定させる。

Freqtradeだけなら重いGPUは不要。AI推論をローカルで重く回す場合だけ、別途GPUや高性能CPUを検討する。初期段階では、ミニPCは取引Botの安定稼働を優先する。

## デプロイ

```bash
cd /opt/hyperliquid-ai-trading
git pull --ff-only
cd freqtrade
docker compose pull
docker compose up -d
docker compose ps
```

## Freqtrade CLIを使う

任意のFreqtradeコマンドは、プロジェクトのラッパーから実行する。

```bash
# 生のFreqtrade CLI
./scripts/ft.sh --help
./scripts/ft.sh list-exchanges

# config.json + config-private.json を自動付与
./scripts/ftc.sh show-config
./scripts/ftc.sh list-pairs --exchange hyperliquid --trading-mode futures --quote USDC --print-list
./scripts/ftc.sh backtesting --strategy HLAiMvpStrategy

# optional dependency image
./scripts/ft-plot.sh plot-profit
./scripts/ft-freqai.sh list-freqaimodels
```

対応範囲は `docs/freqtrade-capabilities.md` を参照。

## ログ確認

```bash
cd /opt/hyperliquid-ai-trading/freqtrade
docker compose logs -f --tail=200 freqtrade
```

## 停止

```bash
cd /opt/hyperliquid-ai-trading/freqtrade
docker compose stop
```

## 日次確認

- Botが起動しているか。
- エラー通知が出ていないか。
- 想定外のポジションを持っていないか。
- ミニPCの空き容量が不足していないか。
- 回線断や再起動が発生していないか。

## 週次確認

- `dry_run` またはライブ成績。
- 最大ドローダウン。
- 勝率ではなく損益比率。
- AIシグナルと実際の値動きのズレ。
- 戦略変更が必要かどうか。

## AIシグナルの扱い

AIは直接発注しない。
ニュース、価格状況、ボラティリティ、相場テーマを読み、Freqtrade戦略が参照する補助シグナルを作る役割に限定する。

初期段階では `freqtrade/user_data/ai_signals/latest.json` を生成するだけでよい。
戦略側では、AIシグナルを「取引条件を少し強める / 弱める」程度に使う。
AIの `confidence` だけで投入額を増やさない。

## リスク管理ルール

- 最初は `max_open_trades: 1` にする。
- 初回の `stake_amount` は小さくする。
- 高レバレッジは使わない。
- ペアはBTCとETHなど流動性が高いものに絞る。
- 損切り条件なしの戦略を動かさない。
- エラー通知が機能していない状態でライブ運用しない。
- 秘密鍵をGitHub、チャット、メモアプリに貼らない。

## 小額ライブ移行条件

- 2週間以上 `dry_run` が安定稼働している。
- 停止、再起動、復旧手順を確認済み。
- エラー通知を受け取れる。
- 1日の最大損失額を決めている。
- API walletの秘密鍵を使っている。
- Bot専用subaccountを使っている。
- 同じ口座で手動売買していない。
- 初回資金は失ってもよい小額に限定している。
