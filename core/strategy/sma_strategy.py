import pandas as pd
from core.strategy import BaseStrategy


class SMAStrategy(BaseStrategy):
    def __init__(self, budget: float):
        super().__init__(budget)
        self.STOP_LOSS_PERCENTAGE = 0.03
        self.TAKE_PROFIT_PERCENTAGE = 0.05

    def signal_buy(self, historical_data: pd.DataFrame, current_price: float) -> float:
        current_sma_50 = historical_data["SMA_50"].iloc[-1]
        current_sma_200 = historical_data["SMA_200"].iloc[-1]
        current_rsi = historical_data["RSI"].iloc[-1]
        if current_sma_50 > current_sma_200 and current_rsi > 30:
            return 1.0  # Strong buy signal
        elif current_sma_50 > current_sma_200:
            return 0.5  # Moderate buy signal
        else:
            return 0.0  # No buy signal

    def signal_sell(self, historical_data: pd.DataFrame, current_price: float) -> float:
        current_sma_50 = historical_data["SMA_50"].iloc[-1]
        current_sma_200 = historical_data["SMA_200"].iloc[-1]
        current_rsi = historical_data["RSI"].iloc[-1]

        if current_sma_50 < current_sma_200 and current_rsi < 70:
            return 1.0  # Strong sell signal
        elif current_sma_50 < current_sma_200:
            return 0.5  # Moderate sell signal
        else:
            return 0.0  # No sell signal

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        data["RSI"] = self.calculate_rsi(data["close"])
        data["MACD"], data["Signal"] = self.calculate_macd(data["close"])
        data["SMA_50"] = data["close"].rolling(window=50).mean()
        data["SMA_200"] = data["close"].rolling(window=200).mean()
        data["ATR"] = self.calculate_atr(data)
        return data

    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        delta = data.diff()
        gain, loss = delta.clip(lower=0), -delta.clip(upper=0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_macd(data: pd.Series):
        ema_12 = data.ewm(span=12, adjust=False).mean()
        ema_26 = data.ewm(span=26, adjust=False).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9, adjust=False).mean()
        return macd, signal

    @staticmethod
    def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
        high, low, close = data["high"], data["low"], data["close"]
        tr = pd.concat(
            [high - low, abs(high - close.shift(1)), abs(low - close.shift(1))], axis=1
        ).max(axis=1)
        return tr.rolling(window=period).mean()

    def check_stop_loss(
        self,
        stock: str,
        current_price: float,
        historical_data: pd.DataFrame,
        positions: dict,
        entry_prices: dict,
        volumes: dict,
        current_date: pd.Timestamp,
    ) -> bool:
        if positions[stock] > 0:
            current_atr = historical_data["ATR"].iloc[-1]
            trailing_stop_loss = entry_prices[stock] - (2 * current_atr)
            if current_price < trailing_stop_loss:
                return True
        return False
