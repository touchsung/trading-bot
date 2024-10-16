from datetime import datetime, time, timedelta
import pytz
from config.settings import settings
from models.market import MarketPhase, PlaceOrder
from database.model import OrderStatus, Trade, SideType
import random


class Market:
    def __init__(self):
        self.bangkok_tz = pytz.timezone("Asia/Bangkok")
        self.market_phases = settings.MARKET_PHASES
        self.holidays = settings.MARKET_HOLIDAYS

    def is_market_open(self, current_time: datetime) -> tuple[bool, MarketPhase]:
        phase = self._get_market_phase(current_time)
        is_open = current_time.weekday() < 5 and not self._is_holiday(
            current_time.date()
        )
        return is_open, phase

    def _is_holiday(self, check_date) -> bool:
        return check_date.strftime("%Y-%m-%d") in self.holidays

    def _get_market_phase(self, current_time: datetime) -> str:
        current_time = current_time.time()
        for phase, times in self.market_phases.items():
            start_times = [time.fromisoformat(t) for t in times["start"]]
            end_time = time.fromisoformat(times["end"])

            for start_time in start_times:
                if start_time <= current_time < end_time:
                    return MarketPhase(phase)

        return "Out of working hours"

    def place_order(self, place_order: PlaceOrder) -> Trade:
        success = random.choices([True, False], weights=[90, 10])[0]
        if success:
            return Trade(
                account_no=place_order.account_no,
                order_no=f"ORDER-{random.randint(1000, 9999)}",
                symbol=place_order.symbol,
                type=place_order.side,
                price=place_order.price,
                volume=place_order.volume,
                commission=(place_order.price * place_order.volume) * 0.001,
                vat=0,
                wht=0,
                trade_date=datetime.now().date(),
                trade_time=datetime.now().time(),
                status=OrderStatus.Matched,
            )
        else:
            return None

    @staticmethod
    def calculate_target_date(date: datetime) -> datetime:
        input_date = date - timedelta(days=1)
        for holiday in reversed(settings.MARKET_HOLIDAYS):
            target_date = input_date.strftime("%Y-%m-%d")
            if target_date == holiday:
                input_date = input_date - timedelta(days=1)
            if input_date.weekday() == 6:
                input_date = input_date - timedelta(days=2)
            elif input_date.weekday() == 5:
                input_date = input_date - timedelta(days=1)

        return input_date
