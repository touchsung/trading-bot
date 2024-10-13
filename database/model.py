from sqlalchemy import Column, String, Date, Time, Float, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


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
