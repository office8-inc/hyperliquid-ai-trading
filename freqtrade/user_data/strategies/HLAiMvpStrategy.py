from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from freqtrade.strategy import IStrategy
from pandas import DataFrame


class HLAiMvpStrategy(IStrategy):
    """Conservative long-only MVP strategy for Hyperliquid dry-run testing."""

    INTERFACE_VERSION = 3

    timeframe = "5m"
    startup_candle_count = 50
    process_only_new_candles = True

    can_short = False

    minimal_roi = {
        "0": 0.02,
        "60": 0.01,
        "180": 0
    }

    stoploss = -0.02
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

    ai_filter_enabled = False
    ai_signal_path = Path("/freqtrade/user_data/ai_signals/latest.json")

    plot_config = {
        "main_plot": {
            "ema_fast": {"color": "blue"},
            "ema_slow": {"color": "orange"}
        },
        "subplots": {
            "RSI": {
                "rsi": {"color": "purple"}
            }
        }
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict[str, Any]) -> DataFrame:
        dataframe["ema_fast"] = dataframe["close"].ewm(span=12, adjust=False).mean()
        dataframe["ema_slow"] = dataframe["close"].ewm(span=26, adjust=False).mean()
        dataframe["rsi"] = self._rsi(dataframe, period=14)
        dataframe["volume_mean"] = dataframe["volume"].rolling(20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict[str, Any]) -> DataFrame:
        technical_entry = (
            (dataframe["ema_fast"] > dataframe["ema_slow"])
            & (dataframe["rsi"] > 45)
            & (dataframe["rsi"] < 70)
            & (dataframe["volume"] > 0)
            & (dataframe["volume"] >= dataframe["volume_mean"] * 0.5)
        )

        dataframe.loc[technical_entry, ["enter_long", "enter_tag"]] = (1, "ema_rsi_long")

        if self.ai_filter_enabled and not self._ai_allows_long(metadata["pair"]):
            dataframe.loc[:, ["enter_long", "enter_tag"]] = (0, None)

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict[str, Any]) -> DataFrame:
        exit_condition = (
            (dataframe["ema_fast"] < dataframe["ema_slow"])
            | (dataframe["rsi"] > 75)
        ) & (dataframe["volume"] > 0)

        dataframe.loc[exit_condition, ["exit_long", "exit_tag"]] = (1, "trend_or_rsi_exit")
        return dataframe

    def leverage(
        self,
        pair: str,
        current_time: datetime,
        current_rate: float,
        proposed_leverage: float,
        max_leverage: float,
        entry_tag: str | None,
        side: str,
        **kwargs,
    ) -> float:
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

    def _load_signal_for_pair(self, pair: str) -> dict[str, Any] | None:
        if not self.ai_signal_path.exists():
            return None

        try:
            payload = json.loads(self.ai_signal_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

        for signal in payload.get("signals", []):
            if signal.get("pair") == pair:
                return signal

        return None
