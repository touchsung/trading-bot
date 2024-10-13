from core.strategy.sma_strategy import SMAStrategy
from core.trading_bot import TradingBot


def main():
    bot = TradingBot(strategy_class=SMAStrategy)
    bot.live_trading()


if __name__ == "__main__":
    main()
