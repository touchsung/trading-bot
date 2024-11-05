from sqlalchemy import (
    Column,
    String,
    Date,
    Time,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    Enum,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship, backref
import enum

Base = declarative_base()


class TimestampMixin:
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SideType(enum.Enum):
    buy = "buy"
    sell = "sell"


class OHLCV(Base):
    __tablename__ = "ohlcv"

    symbol = Column(String, primary_key=True)
    date = Column(Date, primary_key=True)
    time = Column(Time(timezone=True))
    open = Column(Float(8))
    high = Column(Float(8))
    low = Column(Float(8))
    close = Column(Float(8))
    volume = Column(Integer)


class Strategy(Base, TimestampMixin):
    __tablename__ = "strategy"

    strategy_id = Column(Integer, primary_key=True)
    strategy_name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    bots = relationship("Bot", back_populates="strategy")


class Account(Base, TimestampMixin):
    __tablename__ = "account"

    account_no = Column(String, primary_key=True)
    broker = Column(String, nullable=False)
    bots = relationship("Bot", back_populates="account")
    portfolios = relationship("Portfolio", back_populates="account")
    signals = relationship("Signal", back_populates="account")
    trades = relationship("Trade", back_populates="account")


class Bot(Base, TimestampMixin):
    __tablename__ = "bot"

    bot_id = Column(Integer, primary_key=True)
    bot_name = Column(String, nullable=False, unique=True)
    account_no = Column(String, ForeignKey("account.account_no"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategy.strategy_id"), nullable=False)
    trade_symbols = Column(ARRAY(String), nullable=False)
    initial_budget = Column(Float, nullable=False, default=0)
    available_budget = Column(Float, nullable=False, default=0)
    total_profit_loss = Column(Float, nullable=False, default=0)

    account = relationship("Account", back_populates="bots")
    strategy = relationship("Strategy", back_populates="bots")
    signals = relationship("Signal", back_populates="bot")


class Portfolio(Base, TimestampMixin):
    __tablename__ = "portfolio"

    portfolio_id = Column(Integer, primary_key=True)
    account_no = Column(String, ForeignKey("account.account_no"), nullable=False)
    symbol = Column(String, nullable=False)
    entry_price = Column(Float, nullable=False)
    entry_volume = Column(Float, nullable=False)
    average_cost = Column(Float, nullable=False)
    holding_volume = Column(Float, nullable=False)
    profit = Column(Float, nullable=False)

    account = relationship("Account", back_populates="portfolios")


class OrderStatus(enum.Enum):
    Pending = "Pending"
    Open = "Open"
    Matched = "Matched"
    Rejected = "Rejected"
    Cancelled = "Cancelled"
    CancelledByExchange = "Cancelled by Exchange"
    CancelledByBroker = "Cancelled by Broker"
    PendingOpen = "Pending Open"
    PendingCancel = "Pending Cancel"
    NeedApproval = "Need Approval"


class Signal(Base, TimestampMixin):
    __tablename__ = "signal"

    signal_id = Column(Integer, primary_key=True)
    bot_id = Column(Integer, ForeignKey("bot.bot_id"), nullable=False)
    account_no = Column(String, ForeignKey("account.account_no"), nullable=False)
    symbol = Column(String, nullable=False)
    type = Column(Enum(SideType), nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    tp = Column(Float)
    sl = Column(Float)
    position_type = Column(String)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.Pending)
    transaction = relationship("Transaction", back_populates="signal", uselist=False)

    bot = relationship("Bot", back_populates="signals")
    account = relationship("Account", back_populates="signals")


class Trade(Base, TimestampMixin):
    __tablename__ = "trade"

    trade_id = Column(Integer, primary_key=True)
    account_no = Column(String, ForeignKey("account.account_no"), nullable=False)
    order_no = Column(String, nullable=False, unique=True)
    symbol = Column(String, nullable=False)
    type = Column(Enum(SideType), nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    commission = Column(Float, nullable=False)
    vat = Column(Float, nullable=False)
    wht = Column(Float, nullable=False)
    trade_date = Column(Date, nullable=False)
    trade_time = Column(Time, nullable=False)
    status = Column(Enum(OrderStatus), nullable=False)
    transaction = relationship("Transaction", back_populates="trade", uselist=False)

    account = relationship("Account", back_populates="trades")


class Transaction(Base, TimestampMixin):
    __tablename__ = "transaction"

    transaction_id = Column(Integer, primary_key=True)
    trade_id = Column(Integer, ForeignKey("trade.trade_id"), nullable=False)
    signal_id = Column(Integer, ForeignKey("signal.signal_id"), nullable=False)

    trade = relationship("Trade", back_populates="transaction")
    signal = relationship("Signal", back_populates="transaction")
