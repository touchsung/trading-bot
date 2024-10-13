from typing import Dict, Tuple
from datetime import datetime

import pandas as pd

from core.strategy.sma_strategy import SMAStrategy


class TradingBot:
    def __init__(self, data_directory="data", budget=10000, strategy=None):
        self.list_stocks = [
            "AOT",
            "ADVANC",
            "AEONTS",
            "AWC",
            "BANPU",
            "BBL",
            "BDMS",
            "BEM",
            "BGRIM",
            "BH",
        ]
        self.data_directory = data_directory
        self.trades = {stock: [] for stock in self.list_stocks}
        self.dataframes = self._load_all_data()
        self.initial_budget = budget
        self.available_budget = budget
        self.STOP_LOSS_PERCENTAGE = 0.03
        self.TAKE_PROFIT_PERCENTAGE = 0.05
        self.MAX_INVESTMENT_PER_STOCK = budget * 0.05
        self.MAX_TRADE_SIZE = budget * 0.10
        self.MIN_PRICE_THRESHOLD = budget * 0.001
        self.MAX_PRICE_THRESHOLD = budget * 0.1
        self.strategy = strategy or SMAStrategy()

    def _load_all_data(self) -> Dict[str, pd.DataFrame]:
        return {stock: self._load_data(stock) for stock in self.list_stocks}

    def _load_data(self, stock: str) -> pd.DataFrame:
        file_path = f"{self.data_directory}/{stock}.csv"
        try:
            df = pd.read_csv(file_path)
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)
            five_years_ago = pd.Timestamp.now() - pd.DateOffset(years=5)
            return df[df.index >= five_years_ago]
        except FileNotFoundError:
            print(f"Warning: Data for stock {stock} not found at {file_path}.")
            return pd.DataFrame()

    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        delta = data.diff()
        gain, loss = delta.clip(lower=0), -delta.clip(upper=0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_macd(data: pd.Series) -> Tuple[pd.Series, pd.Series]:
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

    def _calculate_indicators(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        historical_data["RSI"] = self.calculate_rsi(historical_data["close"])
        historical_data["MACD"], historical_data["Signal"] = self.calculate_macd(
            historical_data["close"]
        )
        historical_data["SMA_50"] = historical_data["close"].rolling(window=50).mean()
        historical_data["SMA_200"] = historical_data["close"].rolling(window=200).mean()
        historical_data["ATR"] = self.calculate_atr(historical_data)
        return historical_data

    def _trading_logic(self, start_date, end_date):
        positions, entry_prices, volumes, last_trade_date = (
            self._initialize_trading_data()
        )
        all_dates = pd.date_range(start=start_date, end=end_date)

        for current_date in all_dates:
            for stock, df in self.dataframes.items():
                if current_date not in df.index:
                    continue

                self._process_stock_on_date(
                    stock,
                    df,
                    current_date,
                    positions,
                    entry_prices,
                    volumes,
                    last_trade_date,
                )

    def _initialize_trading_data(self):
        positions = {stock: 0 for stock in self.list_stocks}
        entry_prices = {stock: 0 for stock in self.list_stocks}
        volumes = {stock: 0 for stock in self.list_stocks}
        last_trade_date = {stock: None for stock in self.list_stocks}
        return positions, entry_prices, volumes, last_trade_date

    def _process_stock_on_date(
        self, stock, df, current_date, positions, entry_prices, volumes, last_trade_date
    ):
        historical_data = self._calculate_indicators(df.loc[:current_date].copy())
        current_price = historical_data["close"].iloc[-1]

        if not self._is_stock_price_appropriate(stock, current_price):
            return

        current_atr = historical_data["ATR"].iloc[-1]

        if self._check_stop_loss(
            stock,
            current_price,
            current_atr,
            positions,
            entry_prices,
            volumes,
            current_date,
        ):
            return

        self._process_buy_signal(
            stock,
            historical_data,
            current_price,
            current_date,
            positions,
            entry_prices,
            volumes,
            last_trade_date,
        )
        self._process_sell_signal(
            stock, historical_data, current_price, positions, volumes, current_date
        )

    def _process_buy_signal(
        self,
        stock,
        historical_data,
        current_price,
        current_date,
        positions,
        entry_prices,
        volumes,
        last_trade_date,
    ):
        buy_signal = self.strategy.signal_buy(historical_data, current_price)
        if buy_signal > 0:
            if self.available_budget > 0 and self._can_trade(
                stock, current_date, last_trade_date
            ):
                shares_to_buy = self._calculate_shares_to_buy(current_price, buy_signal)
                if shares_to_buy > 0:
                    self._execute_buy(
                        stock,
                        current_price,
                        shares_to_buy,
                        positions,
                        entry_prices,
                        volumes,
                        current_date,
                    )
                    last_trade_date[stock] = current_date

    def _process_sell_signal(
        self, stock, historical_data, current_price, positions, volumes, current_date
    ):
        sell_signal = self.strategy.signal_sell(historical_data, current_price)
        if sell_signal > 0:
            shares_to_sell = int(positions[stock] * sell_signal)
            if shares_to_sell > 0:
                self._execute_sell(
                    stock,
                    current_price,
                    positions,
                    volumes,
                    current_date,
                    shares_to_sell,
                )

    def _can_trade(self, stock, current_date, last_trade_date):
        return (
            last_trade_date[stock] is None
            or (current_date - last_trade_date[stock]).days > 3
        )

    def _calculate_shares_to_buy(self, current_price, buy_signal):
        return min(
            int(self.MAX_TRADE_SIZE / current_price * buy_signal),
            int(self.available_budget / current_price),
        )

    def _execute_buy(
        self,
        stock,
        current_price,
        shares_to_buy,
        positions,
        entry_prices,
        volumes,
        current_date,
    ):
        cost = shares_to_buy * current_price
        if cost <= self.available_budget:
            positions[stock] += shares_to_buy
            entry_prices[stock] = current_price
            self.available_budget -= cost
            volumes[stock] += shares_to_buy
            self.trades[stock].append(
                ("buy", current_date, shares_to_buy, current_price)
            )
            self._log_trade(
                "BUY", stock, current_date, shares_to_buy, current_price, cost
            )

    def _execute_sell(
        self, stock, current_price, positions, volumes, current_date, shares_to_sell
    ):
        if positions[stock] > 0:
            revenue = shares_to_sell * current_price
            positions[stock] -= shares_to_sell
            self.available_budget += revenue
            volumes[stock] += shares_to_sell
            self.trades[stock].append(
                ("sell", current_date, shares_to_sell, current_price)
            )
            self._log_trade(
                "SELL", stock, current_date, shares_to_sell, current_price, revenue
            )

    def _log_trade(self, action, stock, date, shares, price, amount):
        print(
            f"{action:<4}: {date}, Stock: {stock:<6}, Volume: {shares:>4}, "
            f"Price: ${price:.2f}, {'Cost' if action == 'BUY' else 'Revenue'}: ${amount:.2f}"
        )

    def _check_stop_loss(
        self,
        stock,
        current_price,
        current_atr,
        positions,
        entry_prices,
        volumes,
        current_date,
    ):
        if positions[stock] > 0:
            trailing_stop_loss = entry_prices[stock] - (2 * current_atr)
            if current_price < trailing_stop_loss:
                shares_to_sell = positions[stock]
                revenue = shares_to_sell * current_price
                positions[stock] = 0
                self.available_budget += revenue
                volumes[stock] += shares_to_sell
                self.trades[stock].append(
                    ("sell", current_date, shares_to_sell, current_price)
                )
                self._log_trade(
                    "STOP", stock, current_date, shares_to_sell, current_price, revenue
                )
                return True
        return False

    def _is_stock_price_appropriate(self, stock: str, current_price: float) -> bool:
        return self.MIN_PRICE_THRESHOLD <= current_price <= self.MAX_PRICE_THRESHOLD

    def backtest(self, start_date=None, end_date=None):
        if start_date is None:
            start_date = min(df.index.min() for df in self.dataframes.values())
        if end_date is None:
            end_date = max(df.index.max() for df in self.dataframes.values())

        self._trading_logic(start_date, end_date)
        performance = self.evaluate_performance()

        print(f"Backtesting completed for period: {start_date} to {end_date}")
        print("Backtesting Performance:")
        print(f"Total Profit/Loss: ${performance['total_profit_loss']:.2f}")
        print(f"Total Trades: {performance['total_trades']}")
        print(f"Win Rate: {performance['win_rate']:.2f}%")
        print(f"ROI: {performance['roi']:.2f}%")

    def live_trading(self):
        current_date = datetime.now().date()

        # Check if market is open
        if not self._is_market_open(current_date):
            print(f"Market is closed on {current_date}. No trading today.")
            return

        # Update data before trading
        self._update_data()

        self._trading_logic(current_date, current_date)

        # Log trades and update portfolio
        self._log_trades(current_date)
        self._update_portfolio()

        print(f"Real trading completed for {current_date}")

    def _is_market_open(self, date):
        # Implement logic to check if the market is open
        # This is a placeholder implementation
        return date.weekday() < 5  # Assuming market is open Monday to Friday

    def _update_data(self):
        # Implement logic to fetch the latest market data
        # This is a placeholder implementation
        print("Updating market data...")
        # self.dataframes = self._load_all_data()  # Reload all data

    def _log_trades(self, date):
        # Implement logic to log trades for the day
        # This is a placeholder implementation
        print(f"Logging trades for {date}...")
        # Add code to log trades to a file or database

    def _update_portfolio(self):
        # Implement logic to update the portfolio after trading
        # This is a placeholder implementation
        print("Updating portfolio...")
        # Add code to update portfolio values, calculate current positions, etc.

    def evaluate_performance(self) -> Dict[str, float]:
        total_profit_loss = 0
        total_trades = 0
        winning_trades = 0

        for trades in self.trades.values():
            for i in range(0, len(trades), 2):
                if i + 1 < len(trades):
                    buy_trade = trades[i]
                    sell_trade = trades[i + 1]
                    profit_loss = (sell_trade[3] - buy_trade[3]) * buy_trade[2]
                    total_profit_loss += profit_loss
                    total_trades += 1
                    if profit_loss > 0:
                        winning_trades += 1

        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        roi = (total_profit_loss / self.initial_budget) * 100

        return {
            "total_profit_loss": total_profit_loss,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "roi": roi,
        }
