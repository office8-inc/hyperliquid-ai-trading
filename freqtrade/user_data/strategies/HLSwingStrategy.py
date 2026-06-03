from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from freqtrade.strategy import IStrategy, informative
from pandas import DataFrame


class HLSwingStrategy(IStrategy):
    """Long-only SWING strategy for Hyperliquid (BTC/ETH) — 週足/日足/4h の3層。

    長期(週足): 大局トレンド / 中期(日足): セットアップ / 短期(4h): エントリー押し目。
    RSIは日足で過熱判断。ロングオンリー。claudeが4時間ごとに裁量フィルタ(live)。
    最大DD20%は口座全体の別ガード(機械)。パラメータは環境変数で振れる(WFA/グリッド用)。
    """

    INTERFACE_VERSION = 3
    timeframe = "4h"
    can_short = False
    startup_candle_count = 850  # 週足EMA20に必要(20週≒840本の4h)
    process_only_new_candles = True

    minimal_roi = {"0": 0.10, "720": 0.06, "2160": 0.03, "4320": 0.01}
    stoploss = float(os.environ.get("SWING_SL", "-0.06"))
    trailing_stop = True
    trailing_stop_positive = 0.02
    trailing_stop_positive_offset = 0.04
    trailing_only_offset_is_reached = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # 環境変数で振れるパラメータ(グリッド/WFA検証用)
    rsi_entry = float(os.environ.get("SWING_RSI", "48"))      # 4h押し目RSI閾値
    daily_rsi_cap = float(os.environ.get("SWING_DRSI", "72")) # 日足RSI過熱上限
    use_weekly = os.environ.get("SWING_WEEKLY", "1") == "1"   # 週足長期フィルタ on/off

    order_types = {
        "entry": "limit", "exit": "limit", "emergency_exit": "limit",
        "force_entry": "limit", "force_exit": "limit", "stoploss": "limit",
        "stoploss_on_exchange": True, "stoploss_on_exchange_interval": 60,
        "stoploss_on_exchange_limit_ratio": 0.99,
    }

    ai_filter_enabled = True   # live: claude swing filter ON
    ai_signal_path = Path("/freqtrade/user_data/ai_signals/latest.json")

    plot_config = {
        "main_plot": {"ema_fast": {"color": "blue"}, "ema_slow": {"color": "orange"},
                      "ema50_1d": {"color": "gray"}},
        "subplots": {"RSI(4h/1d)": {"rsi": {"color": "purple"}, "rsi_1d": {"color": "red"}},
                     "AI conf": {"ai_confidence": {"color": "green"}}},
    }

    @staticmethod
    def _rsi(dataframe: DataFrame, period: int = 14):
        delta = dataframe["close"].diff()
        gain = delta.clip(lower=0); loss = -delta.clip(upper=0)
        ag = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        al = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        rs = ag / al.replace(0, 1e-10)
        return 100 - (100 / (1 + rs))

    @informative("1w")
    def populate_indicators_1w(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 長期(週足): 大局トレンド
        dataframe["ema20"] = dataframe["close"].ewm(span=20, adjust=False).mean()
        return dataframe

    @informative("1d")
    def populate_indicators_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 中期(日足) + 日足RSI
        dataframe["ema21"] = dataframe["close"].ewm(span=21, adjust=False).mean()
        dataframe["ema50"] = dataframe["close"].ewm(span=50, adjust=False).mean()
        dataframe["rsi"] = self._rsi(dataframe, 14)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict[str, Any]) -> DataFrame:
        dataframe["ema_fast"] = dataframe["close"].ewm(span=12, adjust=False).mean()
        dataframe["ema_slow"] = dataframe["close"].ewm(span=26, adjust=False).mean()
        dataframe["rsi"] = self._rsi(dataframe, 14)
        sig = self._load_signal_for_pair(metadata["pair"])
        dataframe["ai_confidence"] = float(sig.get("confidence", 0)) if sig else 0.0
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict[str, Any]) -> DataFrame:
        cond = (
            (dataframe["ema21_1d"] > dataframe["ema50_1d"])      # 中期(日足)上昇
            & (dataframe["rsi_1d"] < self.daily_rsi_cap)          # 日足RSI過熱でない
            & (dataframe["rsi"] < self.rsi_entry)                 # 短期(4h)押し目
            & (dataframe["close"] > dataframe["open"])            # 反発(陽線)
            & (dataframe["volume"] > 0)
        )
        if self.use_weekly:
            cond = cond & (dataframe["close"] > dataframe["ema20_1w"])  # 長期(週足)大局上昇
        dataframe.loc[cond, ["enter_long", "enter_tag"]] = (1, "swing_dip_long")

        if self.ai_filter_enabled and not self._ai_allows_long(metadata["pair"]):
            dataframe.loc[:, ["enter_long", "enter_tag"]] = (0, None)
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict[str, Any]) -> DataFrame:
        cond = (
            (dataframe["ema21_1d"] < dataframe["ema50_1d"])
            | (dataframe["rsi_1d"] > 78)
            | (dataframe["rsi"] > 72)
        ) & (dataframe["volume"] > 0)
        dataframe.loc[cond, ["exit_long", "exit_tag"]] = (1, "swing_exit")
        return dataframe

    def leverage(self, pair, current_time, current_rate, proposed_leverage,
                 max_leverage, entry_tag, side, **kwargs) -> float:
        return 1.0

    def _resolve_signal_path(self) -> Path:
        ud = self.config.get("user_data_dir")
        return Path(ud) / "ai_signals" / "latest.json" if ud else self.ai_signal_path

    def _load_signal_for_pair(self, pair: str) -> dict[str, Any] | None:
        p = self._resolve_signal_path()
        if not p.exists():
            return None
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        for s in payload.get("signals", []):
            if s.get("pair") == pair:
                return s
        return None

    def _ai_allows_long(self, pair: str) -> bool:
        s = self._load_signal_for_pair(pair)
        if not s:
            return False
        exp = s.get("expires_at")
        if exp:
            try:
                if datetime.fromisoformat(exp.replace("Z", "+00:00")) < datetime.now(timezone.utc):
                    return False
            except ValueError:
                return False
        return (s.get("bias") == "long" and float(s.get("confidence", 0)) >= 0.55
                and s.get("risk") in {"low", "medium"})
