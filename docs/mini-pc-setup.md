# Mini PC Setup Checklist

この手順は、常駐用の別PCで `dry_run` を開始するためのチェックリスト。
このリポジトリは公開テンプレートなので、秘密鍵と実行時データは常駐PC内だけに置く。

## 1. OSと基本設定

推奨OS:

- Ubuntu Server 24.04 LTS または 22.04 LTS

初期設定:

- 有線LANで接続する。
- スリープを無効化する。
- BIOSで停電復帰後の自動起動を有効化する。
- 可能なら小型UPSを接続する。
- SSHはLANまたはVPN経由だけにする。ルーターでSSHをインターネットへ直接公開しない。

## 2. DockerとGitを入れる

Docker EngineとDocker Compose PluginはDocker公式手順で入れる。

- Docker Engine on Ubuntu: https://docs.docker.com/engine/install/ubuntu/
- Docker Compose Plugin: https://docs.docker.com/compose/install/linux/
- Freqtrade Docker Quickstart: https://www.freqtrade.io/en/stable/docker_quickstart/

導入後に確認する。

```bash
git --version
docker --version
docker compose version
```

## 3. リポジトリをcloneする

```bash
sudo mkdir -p /opt/hyperliquid-ai-trading
sudo chown "$USER:$USER" /opt/hyperliquid-ai-trading

git clone https://github.com/office8-inc/hyperliquid-ai-trading.git /opt/hyperliquid-ai-trading
cd /opt/hyperliquid-ai-trading
```

すでにclone済みなら更新する。

```bash
cd /opt/hyperliquid-ai-trading
git pull --ff-only
```

## 4. 秘密設定を常駐PCだけに作る

```bash
cd /opt/hyperliquid-ai-trading
cp freqtrade/user_data/config-private.example.json freqtrade/user_data/config-private.json
```

`freqtrade/user_data/config-private.json` にHyperliquidの値を入れる。

```json
{
  "exchange": {
    "walletAddress": "0xYOUR_MAIN_WALLET_ADDRESS",
    "privateKey": "0xYOUR_API_WALLET_PRIVATE_KEY"
  }
}
```

ルール:

- 本ウォレットの秘密鍵は置かない。
- Bot専用subaccount/API walletを使う。
- Bot稼働中に同じ口座で手動売買しない。
- `config-private.json` はGitHubへpushしない。

## 5. 設定を検証する

```bash
cd /opt/hyperliquid-ai-trading/freqtrade
docker compose config
docker compose pull
```

Freqtrade側の最終設定を確認する。

```bash
cd /opt/hyperliquid-ai-trading
./scripts/ftc.sh show-config
```

Hyperliquidのペアが見えるか確認する。

```bash
./scripts/ftc.sh list-pairs --exchange hyperliquid --trading-mode futures --quote USDC --print-list
```

## 6. dry_runで起動する

初回は必ず `dry_run: true` のまま起動する。

```bash
cd /opt/hyperliquid-ai-trading/freqtrade
docker compose up -d
docker compose ps
docker compose logs -f --tail=200 freqtrade
```

停止する場合:

```bash
cd /opt/hyperliquid-ai-trading/freqtrade
docker compose stop
```

再起動する場合:

```bash
cd /opt/hyperliquid-ai-trading/freqtrade
docker compose up -d
docker compose ps
```

## 7. 初回稼働後に確認する

- コンテナが `Up` になっている。
- `user_data/logs/freqtrade.log` に致命的エラーがない。
- 意図しない実注文が出ていない。
- `dry_run` が有効になっている。
- `BTC/USDC:USDC` と `ETH/USDC:USDC` だけが対象になっている。
- 停止、再起動、復旧ができる。

## 8. 小額ライブ前の必須条件

- 2週間以上 `dry_run` が安定稼働している。
- エラー通知を受け取れる。
- 1日の最大損失額を決めている。
- API walletの秘密鍵を使っている。
- Bot専用subaccountを使っている。
- 同じ口座で手動売買していない。
- 初回資金は失ってもよい小額に限定している。
