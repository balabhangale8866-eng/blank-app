import pandas as pd
from datetime import datetime

class DataManager:
    """Manages tick data and builds 15-minute OHLC candles, tracks day high till 9:30."""

    def __init__(self):
        self.day_high_930 = None
        self.candles_15min = []
        self.current_candle = None

    def add_tick(self, tick: dict):
        """Process incoming tick: update day high and 15-min candle."""
        ts = datetime.now()
        price = tick.get("last_price", 0)
        # Update day high till 9:30
        if ts.time() <= datetime.strptime("09:30:00", "%H:%M:%S").time():
            self.day_high_930 = price if self.day_high_930 is None else max(self.day_high_930, price)
        # Update 15-min candle
        self._update_candle(ts, price, tick.get("volume", 0))

    def _update_candle(self, ts: datetime, price: float, volume: int):
        """Create or update the current 15-min candle."""
        start_min = (ts.minute // 15) * 15
        start = ts.replace(minute=start_min, second=0, microsecond=0)
        if not self.current_candle or self.current_candle["start"] != start:
            # close previous
            if self.current_candle:
                self.candles_15min.append(self.current_candle.copy())
            # start new candle
            self.current_candle = {
                "start": start,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": volume,
            }
        else:
            # update ongoing candle
            c = self.current_candle
            c["high"] = max(c["high"], price)
            c["low"] = min(c["low"], price)
            c["close"] = price
            c["volume"] += volume

    def get_recent_closes(self, n: int = 50) -> pd.Series:
        """Return a Series of the last n close prices (including current)."""
        closes = [c["close"] for c in self.candles_15min[-n:]]
        if self.current_candle:
            closes.append(self.current_candle["close"])
        return pd.Series(closes)