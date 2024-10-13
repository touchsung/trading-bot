import unittest
import pandas as pd
import numpy as np
from core.strategy.sma_strategy import SMAStrategy


class TestSMAStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = SMAStrategy()

    def test_calculate_rsi(self):
        data = pd.Series([10, 12, 11, 13, 14, 15, 16, 15, 14, 13, 12, 11, 10, 9, 8])
        rsi = self.strategy.calculate_rsi(data)
        self.assertEqual(len(rsi), len(data))
        self.assertTrue(all(0 <= x <= 100 for x in rsi.dropna()))

    def test_calculate_macd(self):
        data = pd.Series(np.random.randn(100).cumsum())
        macd, signal = self.strategy.calculate_macd(data)
        self.assertEqual(len(macd), len(data))
        self.assertEqual(len(signal), len(data))

    def test_calculate_atr(self):
        data = pd.DataFrame(
            {
                "high": [10, 11, 12, 13, 14],
                "low": [8, 9, 10, 11, 12],
                "close": [9, 10, 11, 12, 13],
            }
        )
        atr = self.strategy.calculate_atr(data)
        self.assertEqual(len(atr), len(data))
        self.assertTrue(all(x >= 0 for x in atr.dropna()))

    def test_calculate_indicators(self):
        data = pd.DataFrame(
            {
                "high": [10, 11, 12, 13, 14],
                "low": [8, 9, 10, 11, 12],
                "close": [9, 10, 11, 12, 13],
            }
        )
        result = self.strategy.calculate_indicators(data)
        self.assertIn("RSI", result.columns)
        self.assertIn("MACD", result.columns)
        self.assertIn("Signal", result.columns)
        self.assertIn("SMA_50", result.columns)
        self.assertIn("SMA_200", result.columns)
        self.assertIn("ATR", result.columns)

    def test_signal_buy(self):
        data = pd.DataFrame(
            {
                "close": [100, 101, 102, 103, 104],
                "SMA_50": [98, 99, 100, 101, 102],
                "SMA_200": [97, 98, 99, 100, 101],
                "RSI": [40, 45, 50, 55, 60],
            }
        )
        signal = self.strategy.signal_buy(data, 104)
        self.assertIn(signal, [0.0, 0.5, 1.0])

    def test_signal_sell(self):
        data = pd.DataFrame(
            {
                "close": [100, 101, 102, 103, 104],
                "SMA_50": [102, 101, 100, 99, 98],
                "SMA_200": [101, 100, 99, 98, 97],
                "RSI": [60, 65, 70, 75, 80],
            }
        )
        signal = self.strategy.signal_sell(data, 104)
        self.assertIn(signal, [0.0, 0.5, 1.0])

    def test_check_stop_loss(self):
        stock = "AAPL"
        current_price = 95
        historical_data = pd.DataFrame(
            {"close": [100, 101, 102, 103, 104], "ATR": [2, 2, 2, 2, 2]}
        )
        positions = {stock: 10}
        entry_prices = {stock: 100}
        volumes = {stock: 10}
        current_date = pd.Timestamp("2023-01-05")

        result = self.strategy.check_stop_loss(
            stock,
            current_price,
            historical_data,
            positions,
            entry_prices,
            volumes,
            current_date,
        )
        self.assertIsInstance(result, bool)


if __name__ == "__main__":
    unittest.main()
