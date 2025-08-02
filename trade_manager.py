import csv
from datetime import datetime
from typing import List, Dict

class TradeManager:
    """Simulates paper trades, manages PnL, and logs to CSV."""

    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: List[Dict] = []
        self.history: List[Dict] = []
        self.csv_file = "trade_log.csv"
        self._init_csv()

    def _init_csv(self):
        headers = [
            "Timestamp", "Type", "Symbol", "Entry", "SL", "Target",
            "Exit", "Result", "P&L", "CapitalUsed", "Lots", "RunningPnL"
        ]
        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    def place_trade(self, trade_type: str, symbol: str,
                    entry: float, sl: float, target: float, lots: int = 2):
        """Open a new paper trade."""
        cost = entry * lots * 25
        position = {
            "id": len(self.positions),
            "timestamp": datetime.now(),
            "type": trade_type,
            "symbol": symbol,
            "entry": entry,
            "sl": sl,
            "target": target,
            "lots": lots,
            "cost": cost,
            "status": "open",
        }
        self.current_capital -= cost
        self.positions.append(position)
        return position

    def check_exit(self, prices: Dict[str, float]):
        """Check all open positions for SL/target hit."""
        for pos in self.positions[:]:
            if pos["status"] != "open":
                continue
            price = prices.get(pos["symbol"], pos["entry"])
            if price <= pos["sl"]:
                self._close(pos, price, "SL Hit")
            elif price >= pos["target"]:
                self._close(pos, price, "Target Hit")

    def _close(self, pos: Dict, exit_price: float, result: str):
        """Close a position, record PnL, and log."""
        pnl = (exit_price - pos["entry"]) * pos["lots"] * 25
        self.current_capital += pos["cost"] + pnl
        running = self.current_capital - self.initial_capital
        record = {
            "Timestamp": datetime.now(),
            "Type": pos["type"],
            "Symbol": pos["symbol"],
            "Entry": pos["entry"],
            "SL": pos["sl"],
            "Target": pos["target"],
            "Exit": exit_price,
            "Result": result,
            "P&L": pnl,
            "CapitalUsed": pos["cost"],
            "Lots": pos["lots"],
            "RunningPnL": running
        }
        # CSV log
        with open(self.csv_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(record.values())
        # update lists
        pos["status"] = "closed"
        self.history.append(record)
        self.positions.remove(pos)
