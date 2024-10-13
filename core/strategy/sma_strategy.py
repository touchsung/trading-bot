import pandas as pd
from core.strategy import TradingStrategy


class SMAStrategy(TradingStrategy):
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
