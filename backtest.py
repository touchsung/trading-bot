from core.strategy.sma_strategy import SMAStrategy
from core.trading_bot import TradingBot


bot = TradingBot(strategy_class=SMAStrategy)
bot.backtest()
