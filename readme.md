# Trading Bot with SMA Strategy

This README explains the logic and conditions used in our trading bot, which implements a Simple Moving Average (SMA) strategy.

## Trading Bot Logic

The trading bot operates on the following principles:

1. **Initialization**: The bot starts with a predefined budget and a list of stocks to trade.

2. **Data Processing**: For each stock, the bot processes historical price data and calculates necessary indicators.

3. **Trading Loop**: The bot iterates through each date in the specified date range and each stock in the list.

4. **Price Check**: The bot checks if the current stock price is within an appropriate range (defined by `_is_stock_price_appropriate` method).

5. **Stop Loss**: A trailing stop loss is implemented to limit potential losses.

6. **Buy and Sell Signals**: The bot uses the SMA strategy to generate buy and sell signals.

7. **Trade Execution**: Based on the signals, the bot executes buy or sell orders, considering available budget and position limits.

8. **Logging**: All trades are logged for later analysis.

### Key Conditions

- **Trading Frequency**: The bot waits at least 3 days between trades for the same stock.
- **Position Sizing**: The maximum trade size is limited by `MAX_TRADE_SIZE`.
- **Budget Management**: The bot never spends more than the available budget.

## SMA Strategy Logic

The Simple Moving Average (SMA) strategy is implemented in the `SMAStrategy` class. Here are the key components:

1. **Indicators**: The strategy uses two SMAs:

   - Short-term SMA (e.g., 50 days)
   - Long-term SMA (e.g., 200 days)

2. **Buy Signal Conditions**:

   - The short-term SMA crosses above the long-term SMA (Golden Cross)
   - The current price is above both SMAs
   - The long-term SMA is trending upwards

3. **Sell Signal Conditions**:

   - The short-term SMA crosses below the long-term SMA (Death Cross)
   - The current price is below both SMAs
   - The long-term SMA is trending downwards

4. **Signal Strength**: The strategy returns a signal strength (0 to 1) based on how strongly the conditions are met.

### Key Parameters

- `short_window`: The period for the short-term SMA (default: 50)
- `long_window`: The period for the long-term SMA (default: 200)
- `trend_window`: The period for determining the long-term SMA trend (default: 50)

## Risk Management

1. **Stop Loss**: A trailing stop loss is implemented, typically set at 2 ATR (Average True Range) below the entry price.
2. **Position Sizing**: The bot limits the size of each trade to manage risk.
3. **Diversification**: By trading multiple stocks, the bot spreads risk across different assets.

## Performance Evaluation

The bot's performance can be evaluated based on:

- Total return
- Number of trades
- Win rate
- Sharpe ratio
- Maximum drawdown

Remember to backtest the strategy thoroughly and optimize parameters before using it with real money.
