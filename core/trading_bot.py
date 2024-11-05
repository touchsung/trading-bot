import time
from datetime import datetime
from core.discord import Discord
from core.market import Market

import pandas as pd

from core.strategy import BaseStrategy
from database.crud import DB
from models.market import MarketPhase, PlaceOrder
from database.model import (
    Signal,
    SideType,
    OrderStatus,
    Trade,
    Transaction,
    Portfolio,
)
from config.settings import settings
from models.trading_bot import TradingMode


class TradingBot:
    def __init__(self, strategy_class: BaseStrategy, mode: TradingMode):
        self._db = DB()
        self._discord = Discord()
        self._market = Market()
        self._account = settings.ACCOUNT_NO
        self._broker = settings.ACCOUNT_BROKER
        self._strategy = strategy_class()
        self._trading_mode = mode
        self._dataframes = {}
        self._list_stocks = []
        self._trades = {}
        self._initial_budget = 0
        self._available_budget = 0
        self._current_market_phase = None

        # Initialize strategy, account, and bot
        self._strategy_info = self._init_strategy()
        self._account_info = self._init_account()
        self._bot_info = self._load_bot_info()

    def _init_strategy(self):
        return self._db.get_strategy(strategy_name=self._strategy.name)

    def _init_account(self):
        return self._db.get_account(account_no=self._account)

    def _load_bot_info(self):
        return self._db.get_bot_data(
            account_no=self._account_info.account_no,
            strategy_id=self._strategy_info.strategy_id,
        )

    def _prepare_ohlc_data(self):
        self._list_stocks = self._bot_info.trade_symbols
        self._initial_budget = self._bot_info.initial_budget
        self._available_budget = self._bot_info.available_budget

        self._trades = {stock: [] for stock in self._list_stocks}
        self._dataframes = {
            stock: self._load_ohlcv_data(stock) for stock in self._list_stocks
        }
        print("Prepare OHLC data completed")

    def _load_ohlcv_data(self, stock: str) -> pd.DataFrame:
        ohlcv_data = self._db.get_ohlcv_by_symbol(stock)
        if not ohlcv_data:
            print(f"Warning: No data found for stock {stock}.")
            return pd.DataFrame()

        df = pd.DataFrame([vars(record) for record in ohlcv_data])
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        five_years_ago = pd.Timestamp.now() - pd.DateOffset(years=5)
        return df[df.index >= five_years_ago]

    def _load_historical_data(self):
        # Load portfolio data
        portfolios = self._db.get_portfolios_by_account(self._account_info.account_no)
        for portfolio in portfolios:
            if portfolio.symbol in self._list_stocks:
                self._trades[portfolio.symbol].append(
                    {
                        "type": "buy",
                        "date": portfolio.created_at,
                        "price": portfolio.entry_price,
                        "volume": portfolio.holding_volume,
                        "average_cost": portfolio.average_cost,
                    }
                )

        # Load historical trades
        historical_trades = self._db.get_trades_by_account(
            self._account_info.account_no
        )
        for trade in historical_trades:
            if trade.symbol in self._list_stocks:
                self._trades[trade.symbol].append(
                    {
                        "type": trade.type.value,
                        "date": trade.trade_date,
                        "price": trade.price,
                        "volume": trade.volume,
                    }
                )

        # Convert all dates to datetime.date objects
        for stock in self._list_stocks:
            for trade in self._trades[stock]:
                if isinstance(trade["date"], datetime):
                    trade["date"] = trade["date"].date()

        # Sort trades by date for each stock
        for stock in self._list_stocks:
            self._trades[stock].sort(key=lambda x: x["date"])

        print("Historical data loaded")

    def _trading_logic(self, start_date, end_date):
        positions, entry_prices, volumes, last_trade_date = (
            self._initialize_trading_data()
        )
        all_dates = pd.date_range(start=start_date, end=end_date)

        for current_date in all_dates:
            self._alert_log(f"Processing date: {current_date}")
            if self._trading_mode == TradingMode.Live:
                current_date = self._market.calculate_target_date(current_date)
            for stock, df in self._dataframes.items():
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
        positions = {stock: 0 for stock in self._list_stocks}
        entry_prices = {stock: 0 for stock in self._list_stocks}
        volumes = {stock: 0 for stock in self._list_stocks}
        last_trade_date = {stock: None for stock in self._list_stocks}

        if self._trading_mode == TradingMode.Live:
            # Load portfolio data from the database
            portfolios = self._db.get_portfolios_by_account(
                self._account_info.account_no
            )
            for portfolio in portfolios:
                if portfolio.symbol in self._list_stocks:
                    positions[portfolio.symbol] = portfolio.holding_volume
                    entry_prices[portfolio.symbol] = portfolio.average_cost
                    volumes[portfolio.symbol] = portfolio.entry_volume

            # Load last trade dates from the database
            for stock in self._list_stocks:
                last_trade = self._db.get_last_trade_by_symbol(
                    self._account_info.account_no, stock
                )
                if last_trade:
                    last_trade_date[stock] = last_trade.trade_date

        return positions, entry_prices, volumes, last_trade_date

    def _process_stock_on_date(
        self, stock, df, current_date, positions, entry_prices, volumes, last_trade_date
    ):
        historical_data = self._strategy.calculate_indicators(
            df.loc[:current_date].copy()
        )
        current_price = historical_data["close"].iloc[-1]

        if not self._strategy.is_stock_price_appropriate(current_price):
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
        buy_signal, position_type = self._strategy.signal_buy(
            historical_data, current_price
        )
        if buy_signal > 0:
            if self._available_budget > 0:
                shares_to_buy = self._calculate_shares_to_buy(
                    current_price, buy_signal, self._available_budget, stock, positions
                )
                if shares_to_buy > 0:
                    self._execute_buy(
                        stock,
                        current_price,
                        shares_to_buy,
                        positions,
                        entry_prices,
                        volumes,
                        current_date,
                        position_type,
                    )
                    last_trade_date[stock] = current_date

    def _process_sell_signal(
        self, stock, historical_data, current_price, positions, volumes, current_date
    ):
        sell_signal, position_type = self._strategy.signal_sell(
            historical_data, current_price
        )
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
                    position_type,
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
        position_type,
    ):
        cost = shares_to_buy * current_price * (1 + self._market.commission_rate)
        if cost <= self._available_budget:
            if self._trading_mode == TradingMode.Live:
                # Create a new Signal object
                new_signal = Signal(
                    bot_id=self._bot_info.bot_id,
                    account_no=self._account_info.account_no,
                    symbol=stock,
                    type=SideType.buy,
                    price=float(current_price),
                    volume=int(shares_to_buy),
                    position_type=position_type,
                    status=OrderStatus.Pending,
                )

                # Check for duplicate signal
                if not self._db.check_duplicate_signal(new_signal):
                    # Add the signal if it's not a duplicate
                    self._db.add_signal(new_signal)

                    # Place the order
                    order_result = self._place_order(new_signal)

                    if order_result:
                        # Update signal status to Open
                        self._db.update_signal_status(
                            new_signal.signal_id, OrderStatus.Open
                        )

                        # Proceed with the buy execution using order_result values
                        positions[stock] += order_result.volume
                        entry_prices[stock] = order_result.price
                        volumes[stock] += order_result.volume
                        self._trades[stock].append(
                            (
                                "buy",
                                order_result.trade_date,
                                order_result.volume,
                                order_result.price,
                                position_type,
                            )
                        )

                        # Fetch updated budget from database
                        self._bot_info = self._load_bot_info()
                        self._available_budget = self._bot_info.available_budget

                        self._alert_log(
                            f"[BUY]: {order_result.symbol} at {order_result.price} volume {order_result.volume} because {position_type}"
                        )
                    else:
                        # Update signal status to Rejected
                        self._db.update_signal_status(
                            new_signal.signal_id, OrderStatus.Rejected
                        )
                        self._alert_log(f"Buy order for {stock} was rejected.")

                else:
                    self._alert_log(
                        f"Duplicate buy signal for {stock} detected. Skipping execution."
                    )
            else:  # Backtest mode
                positions[stock] += shares_to_buy
                entry_prices[stock] = current_price
                self._available_budget -= cost
                volumes[stock] += shares_to_buy
                self._trades[stock].append(
                    ("buy", current_date, shares_to_buy, current_price, position_type)
                )
                self._alert_log(
                    f"[BUY]: {stock} at {current_price} volume {shares_to_buy} because {position_type}"
                )

    def _execute_sell(
        self,
        stock,
        current_price,
        positions,
        volumes,
        current_date,
        shares_to_sell,
        position_type,
    ):
        if positions[stock] > 0:
            if self._trading_mode == TradingMode.Live:
                # Create a new Signal object
                new_signal = Signal(
                    bot_id=self._bot_info.bot_id,
                    account_no=self._account_info.account_no,
                    symbol=stock,
                    type=SideType.sell,
                    price=float(current_price),
                    volume=int(shares_to_sell),
                    position_type=position_type,
                    status=OrderStatus.Pending,
                )

                # Check for duplicate signal
                if not self._db.check_duplicate_signal(new_signal):
                    # Add the signal if it's not a duplicate
                    self._db.add_signal(new_signal)

                    # Place the order
                    order_result = self._place_order(new_signal)

                    if order_result:
                        # Update signal status to Open
                        self._db.update_signal_status(
                            new_signal.signal_id, OrderStatus.Open
                        )

                        # Proceed with the sell execution
                        positions[stock] -= order_result.volume
                        volumes[stock] += order_result.volume
                        self._trades[stock].append(
                            (
                                "sell",
                                order_result.trade_date,
                                order_result.volume,
                                order_result.price,
                                position_type,
                            )
                        )

                        # Fetch updated budget from database
                        self._bot_info = self._load_bot_info()
                        self._available_budget = self._bot_info.available_budget

                        self._alert_log(
                            f"[SELL]: {order_result.symbol} at {order_result.price} volume {order_result.volume} because {position_type}"
                        )
                    else:
                        # Update signal status to Rejected
                        self._db.update_signal_status(
                            new_signal.signal_id, OrderStatus.Rejected
                        )
                        self._alert_log(f"Sell order for {stock} was rejected.")

                else:
                    self._alert_log(
                        f"Duplicate sell signal for {stock} detected. Skipping execution."
                    )
            else:  # Backtest mode
                revenue = shares_to_sell * current_price
                positions[stock] -= shares_to_sell
                self._available_budget += revenue
                volumes[stock] += shares_to_sell
                self._trades[stock].append(
                    ("sell", current_date, shares_to_sell, current_price, position_type)
                )
                self._alert_log(
                    f"[SELL]: {stock} at {current_price} volume {shares_to_sell} because {position_type}"
                )

    def _place_order(self, signal: Signal) -> Trade | None:
        place_order = PlaceOrder(
            account_no=signal.account_no,
            symbol=signal.symbol,
            side=signal.type,
            price=signal.price,
            volume=signal.volume,
        )

        MAX_RETRIES = 3
        retry_count = 0

        while retry_count < MAX_RETRIES:
            trade_result = self._market.place_order(place_order)
            if trade_result:
                # Add the trade to the database
                new_trade = Trade(
                    account_no=trade_result.account_no,
                    order_no=trade_result.order_no,
                    symbol=trade_result.symbol,
                    type=trade_result.type,
                    price=trade_result.price,
                    volume=trade_result.volume,
                    commission=trade_result.commission,
                    vat=trade_result.vat,
                    wht=trade_result.wht,
                    trade_date=trade_result.trade_date,
                    trade_time=trade_result.trade_time,
                    status=trade_result.status,
                )
                self._db.add_trade(new_trade)

                # Create a transaction to link the signal and trade
                new_transaction = Transaction(
                    trade_id=new_trade.trade_id, signal_id=signal.signal_id
                )
                self._db.add_transaction(new_transaction)

                # Update the signal status to Matched
                self._db.update_signal_status(signal.signal_id, OrderStatus.Matched)

                # Update Bot's budget
                self._update_bot_budget(trade_result)

                # Update Portfolio
                self._update_portfolio(trade_result)

                return trade_result
            else:
                retry_count += 1
                if retry_count < MAX_RETRIES:
                    self._alert_log(
                        f"Retrying order placement for {signal.symbol} (Attempt {retry_count + 1}/{MAX_RETRIES})"
                    )
                    time.sleep(1)  # Add a small delay between retries
                else:
                    self._alert_log(
                        f"Order placement failed after {MAX_RETRIES} attempts for {signal.symbol}"
                    )
                    return None

    def _update_portfolio(self, trade: Trade):
        portfolio = self._db.get_portfolio(trade.account_no, trade.symbol)
        if portfolio:
            if trade.type == SideType.buy:
                # Calculate total trading costs
                total_costs = trade.commission + trade.vat + trade.wht

                # Buy: Update holding volume and average cost (including trading costs)
                portfolio.holding_volume += trade.volume
                total_cost_with_fees = (trade.price * trade.volume) + total_costs
                portfolio.average_cost = (
                    (portfolio.average_cost * (portfolio.holding_volume - trade.volume))
                    + total_cost_with_fees
                ) / portfolio.holding_volume
                # Update profit based on unrealized gains/losses
                portfolio.profit = (
                    trade.price - portfolio.average_cost
                ) * portfolio.holding_volume
            else:  # sell
                # Calculate total trading costs
                total_costs = trade.commission + trade.vat + trade.wht

                # Calculate realized profit for this sale (including trading costs)
                realized_profit = (
                    (trade.price * trade.volume)
                    - (portfolio.average_cost * trade.volume)
                    - total_costs
                )
                portfolio.profit += realized_profit

                # Update holding volume
                portfolio.holding_volume -= trade.volume
                if portfolio.holding_volume == 0:
                    portfolio.average_cost = 0
                # If still holding shares, update unrealized profit
                else:
                    portfolio.profit += (
                        trade.price - portfolio.average_cost
                    ) * portfolio.holding_volume

            self._db.update_portfolio(portfolio)
        else:
            # Calculate total trading costs for initial position
            total_costs = trade.commission + trade.vat + trade.wht
            initial_total_cost = (trade.price * trade.volume) + total_costs
            initial_average_cost = initial_total_cost / trade.volume

            new_portfolio = Portfolio(
                account_no=trade.account_no,
                symbol=trade.symbol,
                entry_price=trade.price,
                entry_volume=trade.volume,
                average_cost=initial_average_cost,  # Include trading costs in average cost
                holding_volume=trade.volume,
                profit=0,  # Initial profit is 0
            )
            self._db.add_portfolio(new_portfolio)

    def _update_bot_budget(self, trade: Trade):
        total_cost = (
            trade.price * trade.volume + trade.commission + trade.vat + trade.wht
        )

        if trade.type == SideType.buy:
            self._bot_info.available_budget -= total_cost
        else:  # sell
            # Calculate profit/loss for this trade
            portfolio = self._db.get_portfolio(trade.account_no, trade.symbol)
            if portfolio:
                trade_profit = (trade.price - portfolio.average_cost) * trade.volume - (
                    trade.commission + trade.vat + trade.wht
                )
                self._bot_info.total_profit_loss += trade_profit
            self._bot_info.available_budget += total_cost

        self._db.update_bot(self._bot_info)

    def _calculate_shares_to_buy(
        self,
        current_price: float,
        buy_signal: float,
        available_budget: float,
        stock: str,
        positions: dict = None,
    ) -> int:
        # Check if we already have a position in this stock
        if self._trading_mode == TradingMode.Live:
            portfolio = self._db.get_portfolio(self._account_info.account_no, stock)
            if portfolio and portfolio.holding_volume > 0:
                return 0
        else:  # Backtest mode
            if positions and positions[stock] > 0:
                return 0

        num_stocks = len(self._list_stocks)
        max_trade_size = (
            0.95 * self._initial_budget
        ) / num_stocks  # 95% of initial budget per stock
        return min(
            int(max_trade_size / current_price * buy_signal),
            int(available_budget / current_price),
        )

    def _alert_log(self, message):
        if self._trading_mode == TradingMode.Live:
            self._discord.send_message_to_discord(
                url=settings.DISCORD_WEBHOOK_URL,
                message=message,
            )

        print(message)

    def backtest(self, start_date=None, end_date=None):
        self._trading_mode = TradingMode.Backtest
        self._prepare_ohlc_data()
        self._load_historical_data()
        self._initial_budget = self._available_budget = 50000
        # Filter out empty dataframes
        non_empty_dfs = {k: df for k, df in self._dataframes.items() if not df.empty}

        if not non_empty_dfs:
            print("No valid data found for backtesting.")
            return

        if start_date is None:
            start_date = min(df.index.min() for df in non_empty_dfs.values())
        if end_date is None:
            end_date = max(df.index.max() for df in non_empty_dfs.values())

        self._trading_logic(start_date, end_date)
        performance = self.evaluate_performance()

        print(f"Backtesting completed for period: {start_date} to {end_date}")
        print("Backtesting Performance:")
        print(f"Initial Budget: ${self._initial_budget:.2f}")
        print(f"Total Profit/Loss: ${performance['total_profit_loss']:.2f}")
        print(f"Total Trades: {performance['total_trades']}")
        print(f"Win Rate: {performance['win_rate']:.2f}%")
        print(f"ROI: {performance['roi']:.2f}%")

    def live_trading(self):
        self._trading_mode = TradingMode.Live
        self._prepare_ohlc_data()
        self._load_historical_data()
        while True:
            current_datetime = datetime.now(self._market.bangkok_tz)
            is_market_open, market_phase = self._market.is_market_open(current_datetime)
            if is_market_open and self._current_market_phase != market_phase:
                self._current_market_phase = market_phase
                if market_phase == MarketPhase.PreOpen:
                    self._prepare_ohlc_data()
                    self._load_historical_data()
                    self._alert_log(f"Initial data loaded at {current_datetime}")
                elif market_phase == MarketPhase.MarketOpen:
                    self._alert_log(f"Market is open at {current_datetime}")
                    current_date = current_datetime.date()
                    self._trading_logic(current_date, current_date)
                elif market_phase == MarketPhase.MarketClose:
                    self._alert_log(f"Market is closed at {current_datetime}")

            time.sleep(60)

    def evaluate_performance(self):
        total_profit_loss = 0
        total_trades = 0
        winning_trades = 0

        for trades in self._trades.values():
            # Convert all trades to a consistent format
            normalized_trades = []
            for trade in trades:
                if isinstance(trade, dict):
                    # Convert dictionary format to tuple format
                    normalized_trades.append(
                        (
                            trade["type"],
                            trade["date"],
                            trade["volume"],
                            trade["price"],
                            "unknown",
                        )
                    )
                else:
                    # Already in tuple format
                    normalized_trades.append(trade)

            # Process trades in pairs
            i = 0
            while i < len(normalized_trades):
                current_trade = normalized_trades[i]

                # Find the next sell trade
                next_sell_index = None
                for j in range(i + 1, len(normalized_trades)):
                    if normalized_trades[j][0] == "sell":
                        next_sell_index = j
                        break

                if next_sell_index is not None:
                    buy_trade = current_trade
                    sell_trade = normalized_trades[next_sell_index]

                    # Calculate profit/loss: (sell_price - buy_price) * volume
                    profit_loss = (sell_trade[3] - buy_trade[3]) * buy_trade[2]
                    total_profit_loss += profit_loss
                    total_trades += 1
                    if profit_loss > 0:
                        winning_trades += 1

                    # Move to the trade after the sell
                    i = next_sell_index + 1
                else:
                    # No matching sell trade found
                    break

        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        roi = (total_profit_loss / self._initial_budget) * 100

        return {
            "total_profit_loss": total_profit_loss,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "roi": roi,
        }
