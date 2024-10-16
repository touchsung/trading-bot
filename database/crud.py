from sqlalchemy import select, and_, update
from sqlalchemy.exc import IntegrityError
from database import SessionLocal
from database.model import (
    OHLCV,
    Signal,
    OrderStatus,
    Strategy,
    Account,
    Bot,
    Trade,
    Transaction,
    Portfolio,
)


class DB:
    def __init__(self):
        self.session = SessionLocal()

    def __del__(self):
        self.session.close()

    # OHLCV table
    def get_ohlcv_by_symbol(self, symbol: str):
        query = select(OHLCV).where(OHLCV.symbol == symbol)
        result = self.session.execute(query).scalars().all()
        return result

    # Strategy table
    def get_strategy(self, strategy_name: str):
        strategy = (
            self.session.query(Strategy).filter_by(strategy_name=strategy_name).first()
        )
        if not strategy:
            raise ValueError(f"Strategy '{strategy_name}' not found.")
        return strategy

    # Account table
    def get_account(self, account_no: str):
        account = self.session.query(Account).filter_by(account_no=account_no).first()
        if not account:
            raise ValueError(f"Account '{account_no}' not found.")
        return account

    # Bot table
    def get_bot(self, bot_name: str):
        bot = self.session.query(Bot).filter_by(bot_name=bot_name).first()
        if not bot:
            raise ValueError(f"Bot '{bot_name}' not found.")
        return bot

    def update_bot(self, bot: Bot):
        try:
            self.session.merge(bot)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise

    def get_bot_data(self, account_no: str, strategy_id: int):
        bot = (
            self.session.query(Bot)
            .filter_by(account_no=account_no, strategy_id=strategy_id)
            .first()
        )
        if not bot:
            raise ValueError(
                f"Bot with account '{account_no}' and strategy_id {strategy_id} not found"
            )
        return bot

    # Signal table
    def check_duplicate_signal(self, signal: Signal):

        query = select(Signal).where(
            and_(
                Signal.bot_id == signal.bot_id,
                Signal.symbol == signal.symbol,
                Signal.type == signal.type,
                Signal.position_type == signal.position_type,
                Signal.status == OrderStatus.Pending,
            )
        )

        result = self.session.execute(query).scalars().first()
        return result is not None

    def add_signal(self, signal: Signal):
        try:
            self.session.add(signal)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise

    def get_pending_signals(self, bot_id: int):
        query = select(Signal).where(
            Signal.bot_id == bot_id, Signal.status != OrderStatus.Open
        )
        result = self.session.execute(query).scalars().all()
        return result

    def update_signal_status(self, signal_id: int, new_status: OrderStatus):
        try:
            stmt = (
                update(Signal)
                .where(Signal.signal_id == signal_id)
                .values(status=new_status)
            )
            self.session.execute(stmt)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise

    # Trade table
    def add_trade(self, trade: Trade):
        try:
            self.session.add(trade)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise

    def get_trades_by_account(self, account_no: str):
        return self.session.query(Trade).filter_by(account_no=account_no).all()

    # Transaction table
    def add_transaction(self, transaction: Transaction):
        try:
            self.session.add(transaction)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise

    # Portfolio table
    def get_portfolios_by_account(self, account_no: str):
        return self.session.query(Portfolio).filter_by(account_no=account_no).all()

    def get_portfolio(self, account_no: str, symbol: str):
        return (
            self.session.query(Portfolio)
            .filter_by(account_no=account_no, symbol=symbol)
            .first()
        )

    def update_portfolio(self, portfolio: Portfolio):
        try:
            self.session.merge(portfolio)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise

    def add_portfolio(self, portfolio: Portfolio):
        try:
            self.session.add(portfolio)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise

    def get_last_trade_by_symbol(self, account_no: str, symbol: str) -> Trade | None:
        return (
            self.session.query(Trade)
            .filter(Trade.account_no == account_no, Trade.symbol == symbol)
            .order_by(Trade.trade_date.desc())
            .first()
        )
