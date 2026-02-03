"""Inline-клавиатуры с CallbackData (aiogram 3)."""

from datetime import date, timedelta
from typing import Optional

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class OrgCb(CallbackData, prefix="org"):
    id: int


class SvcCb(CallbackData, prefix="svc"):
    id: int


class DateCb(CallbackData, prefix="date"):
    dt: str


class SlotCb(CallbackData, prefix="slot"):
    ts: str


class BookingCb(CallbackData, prefix="book"):
    id: str
    action: str


class AdminBookingCb(CallbackData, prefix="adm_book"):
    id: int
    action: str


class AdminCb(CallbackData, prefix="admin"):
    section: str
    id: int


class SubCb(CallbackData, prefix="sub"):
    action: str


def org_list(orgs: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=name, callback_data=OrgCb(id=oid).pack())] for oid, name in orgs]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def service_list(services: list[tuple[int, str, int]]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"{name} ({dur} мин)", callback_data=SvcCb(id=sid).pack())]
        for sid, name, dur in services
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def date_picker(start: Optional[date] = None) -> InlineKeyboardMarkup:
    if start is None:
        start = date.today()
    rows = []
    row = []
    for i in range(14):
        d = start + timedelta(days=i)
        label = d.strftime("%d.%m")
        row.append(InlineKeyboardButton(text=label, callback_data=DateCb(dt=d.isoformat()).pack()))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def slot_list(slots: list[tuple[float, str]]) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for ts, label in slots:
        row.append(InlineKeyboardButton(text=label, callback_data=SlotCb(ts=str(int(ts))).pack()))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_booking() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=BookingCb(id="0", action="confirm").pack()),
                InlineKeyboardButton(text="❌ Отмена", callback_data=BookingCb(id="0", action="cancel").pack()),
            ]
        ]
    )


def client_booking_list(bookings: list[tuple[int, str, str]]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"{label} — {dt}", callback_data=BookingCb(id=str(bid), action="cancel").pack())]
        for bid, label, dt in bookings
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_booking_actions(booking_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=AdminBookingCb(id=booking_id, action="confirm").pack()),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=AdminBookingCb(id=booking_id, action="reject").pack()),
            ],
            [InlineKeyboardButton(text="🕒 Перенести (TODO)", callback_data=AdminBookingCb(id=booking_id, action="reschedule").pack())],
        ]
    )


def admin_menu(org_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Услуги", callback_data=AdminCb(section="services", id=org_id).pack())],
            [InlineKeyboardButton(text="🕐 Расписание", callback_data=AdminCb(section="schedule", id=org_id).pack())],
            [InlineKeyboardButton(text="🚫 Выходные", callback_data=AdminCb(section="blackout", id=org_id).pack())],
            [InlineKeyboardButton(text="📥 Ожидающие брони", callback_data=AdminCb(section="pending", id=org_id).pack())],
            [InlineKeyboardButton(text="📊 Статистика", callback_data=AdminCb(section="stats", id=org_id).pack())],
        ]
    )


def back_to_admin(org_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data=AdminCb(section="menu", id=org_id).pack())]]
    )


def subscription_contact() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📞 Связаться для оплаты", callback_data=SubCb(action="contact").pack())]
        ]
    )
