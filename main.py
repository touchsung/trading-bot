from core.strategy.sma_strategy import SMAStrategy
from core.trading_bot import TradingBot
from models.trading_bot import TradingMode


def main():
    bot = TradingBot(strategy_class=SMAStrategy, mode=TradingMode.Live)
    bot.live_trading()


if __name__ == "__main__":
    main()
