from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from freqtrade.strategy import IStrategy
from pandas import DataFrame


class HLAiMvpStrategy(IStrategy):
    """Long-only DIP-BUY strategy for Hyperliquid dry-run.

    横原さんのスタイル(急落で買い・戻りで利確=逆張り/mean reversion)。
    エントリー: RSI過売り + 直近急落 + 反発の兆し(RSI上昇転換 & 陽線)。
    決済: 戻り(RSI回復 or 平均回帰) + 早めのminimal_ROIで回転。
    AIフィルタ(claude): ai_signals/latest.json の bias=long&conf>=0.55 を「押し目買いGO」として通す。
    可視化: AIシグナルのconfidence/biasとスマートマネーnetをFreqUIチャートのsubplotに出す(現在値)。
    """

    INTERFACE_VERSION = 3

    timeframe = "5m"
    startup_candle_count = 50
    process_only_new_candles = True

    can_short = False

    minimal_roi = {"0": 0.012, "30": 0.006, "90": 0}

    stoploss = -0.025
    trailing_stop = False
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    order_types = {
        "entry": "limit",
        "exit": "limit",
        "emergency_exit": "limit",
        "force_entry": "limit",
        "force_exit": "limit",
        "stoploss": "limit",
        "stoploss_on_exchange": True,
        "stoploss_on_exchange_interval": 60,
        "stoploss_on_exchange_limit_ratio": 0.99,
    }

    ai_filter_enabled = True
    ai_signal_path = Path("/freqtrade/user_data/ai_signals/latest.json")

    plot_config = {
        "main_plot": {
            "ema_fast": {"color": "blue"},
            "ema_slow": {"color": "orange"},
        },
        "subplots": {
            "RSI": {"rsi": {"color": "purple"}},
            "Drop% 30m": {"drop_30m": {"color": "red"}},
            "AI confidence": {
                "ai_confidence": {"color": "green"},
                "ai_long": {"color": "lightgreen"},
            },
            "SmartMoney net $M": {"sm_net_musd": {"color": "teal"}},
        },
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict[str, Any]) -> DataFrame:
        dataframe["ema_fast"] = dataframe["close"].ewm(span=12, adjust=False).mean()
        dataframe["ema_slow"] = dataframe["close"].ewm(span=26, adjust=False).mean()
        dataframe["rsi"] = self._rsi(dataframe, period=14)
        dataframe["volume_mean"] = dataframe["volume"].rolling(20).mean()
        dataframe["drop_30m"] = (dataframe["close"] / dataframe["close"].shift(6) - 1) * 100

        # --- 可視化用: AIシグナル + スマートマネー(現在値を全行へ。FreqUIチャートで確認用) ---
        sig = self._load_signal_for_pair(metadata["pair"])
        dataframe["ai_confidence"] = float(sig.get("confidence", 0)) if sig else 0.0
        dataframe["ai_long"] = 1.0 if (sig and sig.get("bias") == "long") else 0.0
        sm = self._load_smart_money()
        coin = metadata["pair"].split("/")[0]
        if sm and coin in sm:
            dataframe["sm_net_musd"] = round(sm[coin].get("net_usd", 0) / 1_000_000, 2)
        else:
            dataframe["sm_net_musd"] = 0.0
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict[str, Any]) -> DataFrame:
        dip_entry = (
            (dataframe["rsi"] < 35)
            & (dataframe["rsi"] > dataframe["rsi"].shift(1))
            & (dataframe["close"] > dataframe["open"])
            & (dataframe["drop_30m"] < -1.0)
            & (dataframe["volume"] > 0)
            & (dataframe["volume"] >= dataframe["volume_mean"] * 0.5)
        )
        dataframe.loc[dip_entry, ["enter_long", "enter_tag"]] = (1, "dip_buy")

        if self.ai_filter_enabled and not self._ai_allows_long(metadata["pair"]):
            dataframe.loc[:, ["enter_long", "enter_tag"]] = (0, None)
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict[str, Any]) -> DataFrame:
        rebound_exit = (
            (dataframe["rsi"] > 55)
            | (dataframe["close"] >= dataframe["ema_slow"])
        ) & (dataframe["volume"] > 0)
        dataframe.loc[rebound_exit, ["exit_long", "exit_tag"]] = (1, "rebound_exit")
        return dataframe

    def leverage(self, pair, current_time, current_rate, proposed_leverage,
                 max_leverage, entry_tag, side, **kwargs) -> float:
        return 1.0

    @staticmethod
    def _rsi(dataframe: DataFrame, period: int = 14):
        delta = dataframe["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, 1e-10)
        return 100 - (100 / (1 + rs))

    def _ai_allows_long(self, pair: str) -> bool:
        signal = self._load_signal_for_pair(pair)
        if not signal:
            return False
        expires_at = signal.get("expires_at")
        if expires_at:
            try:
                expires = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                if expires < datetime.now(timezone.utc):
                    return False
            except ValueError:
                return False
        return (
            signal.get("bias") == "long"
            and float(signal.get("confidence", 0)) >= 0.55
            and signal.get("risk") in {"low", "medium"}
        )

    def _resolve_signal_path(self) -> Path:
        user_dir = self.config.get("user_data_dir")
        if user_dir:
            return Path(user_dir) / "ai_signals" / "latest.json"
        return self.ai_signal_path

    def _read_payload(self) -> dict[str, Any] | None:
        signal_path = self._resolve_signal_path()
        if not signal_path.exists():
            return None
        try:
            return json.loads(signal_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def _load_signal_for_pair(self, pair: str) -> dict[str, Any] | None:
        payload = self._read_payload()
        if not payload:
            return None
        for signal in payload.get("signals", []):
            if signal.get("pair") == pair:
                return signal
        return None

    def _load_smart_money(self) -> dict[str, Any] | None:
        payload = self._read_payload()
        return payload.get("smart_money") if payload else None
