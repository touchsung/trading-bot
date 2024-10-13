import unittest
from unittest.mock import Mock, patch
import pandas as pd
from datetime import datetime, timedelta
from core.trading_bot import TradingBot
from core.strategy.sma_strategy import SMAStrategy


class TestTradingBot(unittest.TestCase):
    def setUp(self):
        self.strategy = SMAStrategy()
        self.bot = TradingBot(strategy=self.strategy)

    def test_init(self):
        self.assertIsInstance(self.bot.strategy, SMAStrategy)
        self.assertEqual(self.bot.initial_budget, 10000)
        self.assertEqual(self.bot.available_budget, 10000)

    @patch("core.trading_bot.TradingBot._load_data")
    def test_load_all_data(self, mock_load_data):
        mock_df = pd.DataFrame({"close": [100, 101, 102]})
        mock_load_data.return_value = mock_df

        result = self.bot._load_all_data()

        self.assertEqual(len(result), len(self.bot.list_stocks))
        for df in result.values():
            pd.testing.assert_frame_equal(df, mock_df)

    def test_initialize_trading_data(self):
        positions, entry_prices, volumes, last_trade_date = (
            self.bot._initialize_trading_data()
        )

        self.assertEqual(len(positions), len(self.bot.list_stocks))
        self.assertEqual(len(entry_prices), len(self.bot.list_stocks))
        self.assertEqual(len(volumes), len(self.bot.list_stocks))
        self.assertEqual(len(last_trade_date), len(self.bot.list_stocks))

        for stock in self.bot.list_stocks:
            self.assertEqual(positions[stock], 0)
            self.assertEqual(entry_prices[stock], 0)
            self.assertEqual(volumes[stock], 0)
            self.assertIsNone(last_trade_date[stock])

    @patch("core.trading_bot.TradingBot._execute_buy")
    @patch("core.trading_bot.TradingBot._execute_sell")
    def test_process_stock_on_date(self, mock_execute_sell, mock_execute_buy):
        stock = "AAPL"
        df = pd.DataFrame(
            {
                "close": [100, 101, 102, 103, 104],
                "high": [105, 106, 107, 108, 109],
                "low": [95, 96, 97, 98, 99],
            },
            index=pd.date_range(start="2023-01-01", periods=5),
        )

        current_date = pd.Timestamp("2023-01-05")
        positions = {stock: 0}
        entry_prices = {stock: 0}
        volumes = {stock: 0}
        last_trade_date = {stock: None}

        self.strategy.signal_buy = Mock(return_value=1.0)
        self.strategy.signal_sell = Mock(return_value=0.0)
        self.strategy.check_stop_loss = Mock(return_value=False)

        self.bot._process_stock_on_date(
            stock, df, current_date, positions, entry_prices, volumes, last_trade_date
        )

        mock_execute_buy.assert_called_once()
        mock_execute_sell.assert_not_called()

    def test_evaluate_performance(self):
        self.bot.trades = {
            "AAPL": [
                ("buy", datetime(2023, 1, 1), 10, 100),
                ("sell", datetime(2023, 1, 2), 10, 110),
                ("buy", datetime(2023, 1, 3), 5, 105),
                ("sell", datetime(2023, 1, 4), 5, 100),
            ]
        }
        self.bot.initial_budget = 10000

        performance = self.bot.evaluate_performance()

        self.assertEqual(performance["total_profit_loss"], 75)
        self.assertEqual(performance["total_trades"], 2)
        self.assertEqual(performance["win_rate"], 50)
        self.assertAlmostEqual(performance["roi"], 0.75)


if __name__ == "__main__":
    unittest.main()
