from abc import ABC, abstractmethod

import pandas as pd


class TradingStrategy(ABC):
    @abstractmethod
    def signal_buy(self, historical_data: pd.DataFrame, current_price: float) -> float:
        pass

    @abstractmethod
    def signal_sell(self, historical_data: pd.DataFrame, current_price: float) -> float:
        pass
