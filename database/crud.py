from sqlalchemy import select
from database import SessionLocal
from database.model import OHLCV


class DB:
    def __init__(self):
        self.session = SessionLocal()

    def __del__(self):
        self.session.close()

    def get_ohlcv_by_symbol(self, symbol: str):
        query = select(OHLCV).where(OHLCV.symbol == symbol)
        result = self.session.execute(query).scalars().all()
        return result
