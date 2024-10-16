from core.strategy.sma_strategy import SMAStrategy
from core.trading_bot import TradingBot
from models.trading_bot import TradingMode


bot = TradingBot(strategy_class=SMAStrategy, mode=TradingMode.Backtest)
bot.backtest()
