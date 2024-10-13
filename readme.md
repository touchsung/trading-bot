# Algorithmic Trading Bot

This project implements an algorithmic trading bot that can perform backtesting and live trading using various strategies.

## Project Structure

├── core/
│ ├── strategy/
│ │ ├── init.py
│ │ ├── base_strategy.py
│ │ └── sma_strategy.py
│ └── trading_bot.py
├── data/
│ └── [stock_symbol].csv
├── main.py
└── README.md

## Components

### TradingBot (core/trading_bot.py)

The main class that handles the trading logic, data management, and execution of trades. It uses a strategy object to determine buy and sell signals.

Key features:

- Loads and manages historical stock data
- Implements backtesting functionality
- Supports live trading (placeholder implementation)
- Calculates and reports performance metrics

### BaseStrategy (core/strategy/base_strategy.py)

An abstract base class that defines the interface for all trading strategies.

Key methods:

- `signal_buy`: Determines buy signals
- `signal_sell`: Determines sell signals
- `calculate_indicators`: Computes technical indicators
- `check_stop_loss`: Implements stop-loss logic

### SMAStrategy (core/strategy/sma_strategy.py)

A concrete implementation of BaseStrategy that uses Simple Moving Averages (SMA) and Relative Strength Index (RSI) for trading decisions.

Key features:

- Implements SMA crossover strategy
- Uses RSI for overbought/oversold conditions
- Calculates additional indicators like MACD and ATR

## Usage

1. Ensure you have the required data files in the `data/` directory.
2. Modify the `main.py` file to use the desired strategy and trading mode.
3. Run the bot using:

```bash
python main.py
```

## Extending the Bot

To create a new trading strategy:

1. Create a new file in the `core/strategy/` directory (e.g., `my_strategy.py`).
2. Define a new class that inherits from `BaseStrategy`.
3. Implement the required methods (`signal_buy`, `signal_sell`, `calculate_indicators`, `check_stop_loss`).
4. Update `main.py` to use your new strategy.

## Dependencies

- pandas
- numpy (used indirectly by pandas)

## Future Improvements

- Implement real-time data fetching for live trading
- Add more sophisticated strategies
- Improve risk management features
- Implement portfolio optimization
- Add unit tests and integration tests

## Disclaimer

This trading bot is for educational purposes only. Always perform your own research and risk assessment before engaging in real trading.
