# Operation Manual

## 役割分担

| 環境 | 役割 |
| --- | --- |
| GitHub | コード、設定テンプレート、手順書を管理 |
| Windows PC | 開発、ドキュメント編集、短時間検証 |
| 自宅ミニPC | FreqtradeをDockerで24H稼働 |

## ミニPC初期セットアップ

1. Ubuntu Server系Linuxを入れる。
2. 有線LANで接続する。
3. スリープを無効化する。
4. BIOSで停電復帰時の自動起動を有効化する。
5. SSHはLANまたはVPN経由だけにする。
6. Docker Engine、Docker Compose Plugin、Gitを入れる。

## デプロイ

```bash
cd /opt/hyperliquid-ai-trading
git pull --ff-only
cd freqtrade
docker compose pull
docker compose up -d
docker compose ps
```

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

## 小額ライブ移行条件

- 2週間以上 `dry_run` が安定稼働している。
- 停止、再起動、復旧手順を確認済み。
- エラー通知を受け取れる。
- 1日の最大損失額を決めている。
- API walletの秘密鍵を使っている。
- 初回資金は失ってもよい小額に限定している。
