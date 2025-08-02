from kiteconnect import KiteConnect
from typing import Dict, List

class OptionsManager:
    """Fetches ATM option symbols and live quotes."""

    def __init__(self, kite: KiteConnect):
        self.kite = kite
        self.sensex_token = None

    def _fetch_instruments(self) -> List[dict]:
        """Download BSE F&O instrument list (cache in memory)."""
        if not hasattr(self, "_instruments"):
            self._instruments = self.kite.instruments("BFO")
        return self._instruments

    def get_sensex_token(self) -> int:
        """Get the Sensex index instrument token."""
        if self.sensex_token:
            return self.sensex_token
        for inst in self.kite.instruments("BSE"):
            if inst["name"] == "SENSEX":
                self.sensex_token = inst["instrument_token"]
                break
        return self.sensex_token

    def get_atm_symbols(self, spot: float) -> Dict[str, str]:
        """
        Return ATM CE & PE symbols.
        Rounds spot to nearest 100 for Sensex strikes.
        """
        strike = round(spot / 100) * 100
        ce, pe = None, None
        for inst in self._fetch_instruments():
            if inst["name"] == "SENSEX" and inst["strike"] == strike:
                if inst["instrument_type"] == "CE":
                    ce = inst["tradingsymbol"]
                elif inst["instrument_type"] == "PE":
                    pe = inst["tradingsymbol"]
        return {"CE": ce, "PE": pe}

    def get_option_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Fetch last_price for given option symbols."""
        quotes = self.kite.quote(symbols)
        return {sym: quotes[sym]["last_price"] for sym in symbols if sym in quotes}
