from abc import ABC, abstractmethod

import pandas as pd


class BaseStrategy(ABC):
    def __init__(self):
        self.MIN_PRICE_THRESHOLD = 10
        self.MAX_PRICE_THRESHOLD = 1000
        self.MAX_TRADE_SIZE = 1000

    @abstractmethod
    def signal_buy(self, historical_data: pd.DataFrame, current_price: float) -> float:
        pass

    @abstractmethod
    def signal_sell(self, historical_data: pd.DataFrame, current_price: float) -> float:
        pass

    @abstractmethod
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        pass

    def is_stock_price_appropriate(self, current_price: float) -> bool:
        return self.MIN_PRICE_THRESHOLD <= current_price <= self.MAX_PRICE_THRESHOLD

    def calculate_shares_to_buy(
        self, current_price: float, buy_signal: float, available_budget: float
    ) -> int:
        return min(
            int(self.MAX_TRADE_SIZE / current_price * buy_signal),
            int(available_budget / current_price),
        )

    @abstractmethod
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
        pass
