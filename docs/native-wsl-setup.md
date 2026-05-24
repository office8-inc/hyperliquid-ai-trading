# Native WSL Setup Checklist

この手順は、既存の常駐PCでDockerを入れずに、WSL2 Ubuntu上でFreqtradeを動かすためのチェックリスト。
Slack WebSocketやCloudflare Tunnelがすでに動いているcrow-bot機では、Docker daemonと追加ネットワークルールを避けるため、この構成を優先する。

## 対象環境

ユーザー確認済みの前提:

- ホストOS: Windows 10 Pro 22H2
- WSL: 2.7.3.0
- WSL distro: `Ubuntu-24.04`
- Ubuntu: 24.04.3 LTS
- CPU architecture: `x86_64`
- Python: 3.12.3
- Git: 2.43.0
- init: `systemd`

Freqtrade公式ドキュメントではWindows環境はDocker推奨だが、Dockerを使えない場合はWSLでUbuntu/Linux手順を使う方針が案内されている。
このPCはWSL2、x86_64、Python 3.12、systemdが揃っているため、native WSL構成で進められる。

## セキュリティ方針

常駐PCにはSlack WebSocket、Cloudflare Tunnel、Claude Codeなど外部入力を受ける仕組みがあるため、取引用の秘密情報は分離して扱う。

必須:

- FreqtradeはBot専用のLinuxユーザーで動かす。
- HyperliquidはBot専用subaccount/API walletを使う。
- 本ウォレットの秘密鍵は置かない。
- `freqtrade/user_data/config-private.json` はGitに入れない。
- `config-private.json` は所有者だけ読める権限にする。
- Freqtrade API server / Web UIは初期状態で無効のままにする。
- Cloudflare TunnelでFreqtrade API server / Web UIを公開しない。
- `show-config` の全文をチャットへ貼らない。秘密値が混ざる可能性がある。

推奨ユーザー名は `trading`。
既存のClaude Codeやcrow-botが `seiya` で動いている場合、同じ `seiya` に取引秘密鍵を置くと読み取り可能になるため、分離効果が弱い。

```bash
sudo adduser --disabled-password --gecos "" trading
```

管理作業は `seiya` などsudo可能なユーザーで行い、Botプロセスと秘密ファイルの所有者は `trading` にする。

## 1. OSパッケージを入れる

公式手順の前提に合わせ、Ubuntu側で最低限の依存を入れる。

```bash
sudo apt update
sudo apt install -y git curl python3-pip python3-venv python3-dev python3-pandas
```

時刻ズレは取引所API通信の問題になるため、Windows側とWSL側の時刻同期が正常であることを確認する。

```bash
timedatectl status
```

## 2. Freqtrade本体を入れる

このリポジトリにはFreqtrade本体を置かない。
Freqtrade本体は `/opt/freqtrade` にcloneし、プロジェクトのラッパーから呼び出す。

初回は、Freqtrade公式が推奨する `stable` branchを使う。
2026-05-24時点の最新リリースは `2026.4` なので、インストール後の `freqtrade --version` がこのリポジトリで使うDocker imageと揃っているか確認する。
将来更新するときは、Docker image、native Freqtrade、ドキュメントを同時に更新する。

```bash
sudo mkdir -p /opt/freqtrade
sudo chown -R "$USER:$USER" /opt/freqtrade

git clone https://github.com/freqtrade/freqtrade.git /opt/freqtrade
cd /opt/freqtrade
git checkout stable
./setup.sh -i
```

公式の `setup.sh -i` は、依存パッケージの導入と `.venv/` 作成を行う。
途中でsudoや確認入力を求められた場合は、内容を確認して進める。

インストール後に確認する。

```bash
/opt/freqtrade/.venv/bin/freqtrade --version
```

Bot実行ユーザーがFreqtrade本体を読めるように所有者を揃える。

```bash
sudo chown -R trading:trading /opt/freqtrade
```

## 3. このリポジトリをcloneする

```bash
sudo mkdir -p /opt/hyperliquid-ai-trading
sudo chown -R trading:trading /opt/hyperliquid-ai-trading

sudo -iu trading
git clone https://github.com/office8-inc/hyperliquid-ai-trading.git /opt/hyperliquid-ai-trading
cd /opt/hyperliquid-ai-trading
```

すでにclone済みなら更新する。

```bash
cd /opt/hyperliquid-ai-trading
git pull --ff-only
```

## 4. 秘密設定を作る

```bash
cd /opt/hyperliquid-ai-trading
cp freqtrade/user_data/config-private.example.json freqtrade/user_data/config-private.json
chmod 600 freqtrade/user_data/config-private.json
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

確認する。

```bash
ls -l freqtrade/user_data/config-private.json
git status --short
```

`git status --short` に `config-private.json` が出ないことを確認する。

## 5. Nativeラッパーで検証する

```bash
cd /opt/hyperliquid-ai-trading

./scripts/ft-native.sh --version
./scripts/ftc-native.sh show-config
```

`show-config` は画面上で確認するだけにし、全文をチャットやログへ貼らない。

HyperliquidのUSDC建てfuturesペアが見えるか確認する。

```bash
./scripts/ftc-native.sh list-pairs --exchange hyperliquid --trading-mode futures --quote USDC --print-list
```

`BTC/USDC:USDC` と `ETH/USDC:USDC` が見えることを確認する。

## 6. 手動でdry_run起動する

初回は必ず `dry_run: true` のまま起動する。

```bash
cd /opt/hyperliquid-ai-trading
./scripts/ftc-native.sh trade \
  --logfile user_data/logs/freqtrade.log \
  --db-url sqlite:///user_data/tradesv3.sqlite \
  --strategy HLAiMvpStrategy
```

別ターミナルでログを確認する。

```bash
tail -f /opt/hyperliquid-ai-trading/freqtrade/user_data/logs/freqtrade.log
```

止めるときは、起動中のターミナルで `Ctrl+C`。

## 7. systemdサービス化する

手動起動が成功してからサービス化する。

```bash
exit
sudo cp /opt/hyperliquid-ai-trading/deploy/freqtrade-wsl.service.example /etc/systemd/system/freqtrade-wsl.service
sudo systemctl daemon-reload
sudo systemctl enable --now freqtrade-wsl.service
systemctl status freqtrade-wsl.service --no-pager
```

`trading` 以外のユーザー名で動かす場合は、`/etc/systemd/system/freqtrade-wsl.service` の `User=` と `Group=` を変更し、`/opt/freqtrade` と `/opt/hyperliquid-ai-trading` の所有者も揃える。

ログ確認:

```bash
journalctl -u freqtrade-wsl.service -f
```

停止:

```bash
sudo systemctl stop freqtrade-wsl.service
```

設定変更後の再起動:

```bash
sudo systemctl restart freqtrade-wsl.service
```

## 8. Windows起動時にWSLサービスを起動する

WSL内で `systemctl enable` しても、Windows起動直後にWSL distroが必ず自動起動するとは限らない。
Windowsのタスクスケジューラで、ログオン時または起動時に以下を実行する。

```powershell
powershell.exe -ExecutionPolicy Bypass -File "\\wsl$\Ubuntu-24.04\opt\hyperliquid-ai-trading\deploy\start-freqtrade-wsl.ps1"
```

手動実行で確認する場合:

```powershell
powershell.exe -ExecutionPolicy Bypass -File "\\wsl$\Ubuntu-24.04\opt\hyperliquid-ai-trading\deploy\start-freqtrade-wsl.ps1"
```

## 9. 日次確認

```bash
systemctl is-active freqtrade-wsl.service
journalctl -u freqtrade-wsl.service -n 100 --no-pager
df -h /opt/hyperliquid-ai-trading
```

確認項目:

- サービスが `active`。
- `dry_run` が有効。
- 対象ペアが `BTC/USDC:USDC` と `ETH/USDC:USDC`。
- 意図しない実注文がない。
- ログに認証エラー、APIレート制限、DBエラーがない。
- WSLとWindowsの時刻が大きくズレていない。

## 10. 既存crow-bot機への影響

この構成で追加する常駐要素は、WSL内の `freqtrade-wsl.service` と `/opt/freqtrade` / `/opt/hyperliquid-ai-trading` 配下のファイル。
Docker daemon、Docker bridge、Windows側の追加ポート公開は使わない。

影響を避けるためのルール:

- 既存のCloudflare Tunnel設定は変更しない。
- Freqtrade API server / Web UIをTunnelに追加しない。
- Slack WebSocketやホームページ自販機のプロセスと同じユーザーに秘密鍵を置かない。
- 取引Botの停止・再起動は `freqtrade-wsl.service` だけに限定する。

## 参照

- Freqtrade Installation: https://docs.freqtrade.io/en/stable/installation/
- Freqtrade Release 2026.4: https://github.com/freqtrade/freqtrade/releases/tag/2026.4
