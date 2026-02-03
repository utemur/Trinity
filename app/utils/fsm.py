"""FSM состояния для бронирования."""

from aiogram.fsm.state import State, StatesGroup


class BookingStates(StatesGroup):
    choosing_org = State()
    choosing_service = State()
    choosing_date = State()
    choosing_slot = State()
    entering_name = State()
    entering_phone = State()
    confirming = State()


class CancelBookingStates(StatesGroup):
    choosing_booking = State()
    confirming = State()


class AdminStates(StatesGroup):
    adding_service_name = State()
    adding_service_duration = State()
    adding_service_price = State()
    adding_rule_weekday = State()
    adding_rule_start = State()
    adding_rule_end = State()
    adding_rule_step = State()
    adding_blackout_start = State()
    adding_blackout_end = State()
