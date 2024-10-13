from core.strategy.sma_strategy import SMAStrategy
from core.trading_bot import TradingBot


def main():
    strategy = SMAStrategy()
    bot = TradingBot(strategy=strategy)

    # For backtesting
    bot.backtest()

    # For production trading
    # bot.live_trading()


if __name__ == "__main__":
    main()
