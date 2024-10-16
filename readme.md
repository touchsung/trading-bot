# Algorithmic Trading Bot

This project implements an algorithmic trading bot that can perform backtesting and live trading using various strategies.

## Project Structure

├── core/
│ ├── strategy/
│ │ ├── init.py
│ │ ├── base_strategy.py
│ │ └── sma_strategy.py
│ ├── discord.py
│ ├── market.py
│ └── trading_bot.py
├── database/
│ ├── init.py
│ ├── crud.py
│ └── model.py
├── models/
│ ├── market.py
│ └── trading_bot.py
├── config/
│ └── settings.py
├── backtest.py
├── main.py
├── requirements.txt
└── README.md

## Components

### TradingBot (core/trading_bot.py)

The main class that handles the trading logic, data management, and execution of trades. It uses a strategy object to determine buy and sell signals.

Key features:

- Supports both backtesting and live trading modes
- Loads and manages historical stock data
- Implements backtesting functionality
- Supports live trading with real-time order placement
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

### Market (core/market.py)

Handles market-related operations and simulates order placement for live trading.

Key features:

- Checks if the market is open
- Determines the current market phase
- Simulates order placement

### Database (database/)

Manages database operations using SQLAlchemy ORM.

Key components:

- `model.py`: Defines database models
- `crud.py`: Implements CRUD operations

### Config (config/settings.py)

Manages configuration settings using Pydantic.

### Discord (core/discord.py)

Handles sending alerts and messages to Discord.

## Usage

1. Install the required dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Set up your environment variables in a `.env` file based on the `example.env` file.

3. To run backtesting:

   ```
   python backtest.py
   ```

4. To run live trading:
   ```
   python main.py
   ```

## Extending the Bot

To create a new trading strategy:

1. Create a new file in the `core/strategy/` directory (e.g., `my_strategy.py`).
2. Define a new class that inherits from `BaseStrategy`.
3. Implement the required methods (`signal_buy`, `signal_sell`, `calculate_indicators`, `check_stop_loss`).
4. Update `backtest.py` or `main.py` to use your new strategy.

## Future Improvements

- Implement real-time data fetching for live trading
- Add more sophisticated strategies
- Improve risk management features
- Implement portfolio optimization
- Add more comprehensive unit tests and integration tests
- Implement logging for better debugging and monitoring

## Disclaimer

This trading bot is for educational purposes only. Always perform your own research and risk assessment before engaging in real trading.
