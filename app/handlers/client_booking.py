"""Обработчики бронирования для клиентов."""

import logging
from datetime import datetime
from typing import Any, Dict

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.db.repo import BookingRepo, OrganizationRepo, ServiceRepo, SubscriptionRepo
from app.keyboards.inline import (
    admin_booking_actions,
    BookingCb,
    DateCb,
    date_picker,
    OrgCb,
    service_list,
    SvcCb,
    SlotCb,
    slot_list,
)
from app.keyboards.reply import BOOK, CANCEL_BOOKING, MY_BOOKINGS
from app.services.booking_service import BookingService
from app.services.validation import validate_name, validate_phone
from app.utils.fsm import BookingStates, CancelBookingStates

logger = logging.getLogger(__name__)
router = Router(name="client_booking")


@router.message(F.text == BOOK)
async def start_booking(message: Message, state: FSMContext, session) -> None:
    await state.clear()
    orgs = await OrganizationRepo.get_all(session)
    if not orgs:
        await message.answer("Нет доступных организаций.")
        return

    if len(orgs) == 1:
        await state.update_data(org_id=orgs[0].id)
        await _show_services(message, state, session)
        return

    from app.keyboards.inline import org_list

    await state.set_state(BookingStates.choosing_org)
    await message.answer("Выберите организацию:", reply_markup=org_list([(o.id, o.name) for o in orgs]))


@router.callback_query(OrgCb.filter(), BookingStates.choosing_org)
async def on_org_selected(cq: CallbackQuery, callback_data: OrgCb, state: FSMContext, session) -> None:
    org_id = callback_data.id
    await state.update_data(org_id=org_id)
    await state.set_state(BookingStates.choosing_service)
    await _show_services_msg(cq, state, session)


async def _show_services(message_or_cq, state: FSMContext, session) -> None:
    data = await state.get_data()
    org_id = data["org_id"]
    sub = await SubscriptionRepo.get_by_org(session, org_id)
    from datetime import datetime
    from zoneinfo import ZoneInfo
    now = datetime.now(ZoneInfo("UTC"))
    if not sub or sub.status != "ACTIVE":
        text = "У сервиса закончилась подписка. Бронирование временно недоступно."
        if hasattr(message_or_cq, "answer"):
            await message_or_cq.answer(text)
        else:
            await message_or_cq.message.edit_text(text)
        await state.clear()
        return
    end = sub.current_period_end
    if end.tzinfo is None:
        end = end.replace(tzinfo=ZoneInfo("UTC"))
    if end < now:
        text = "У сервиса закончилась подписка. Бронирование временно недоступно."
        if hasattr(message_or_cq, "answer"):
            await message_or_cq.answer(text)
        else:
            await message_or_cq.message.edit_text(text)
        await state.clear()
        return

    services = await ServiceRepo.get_by_org(session, org_id)
    if not services:
        text = "Нет доступных услуг."
        if hasattr(message_or_cq, "answer"):
            await message_or_cq.answer(text)
        else:
            await message_or_cq.message.edit_text(text)
        await state.clear()
        return

    kb = service_list([(s.id, s.name, s.duration_minutes) for s in services])
    if hasattr(message_or_cq, "answer"):
        await message_or_cq.answer("Выберите услугу:", reply_markup=kb)
    else:
        await message_or_cq.message.edit_text("Выберите услугу:", reply_markup=kb)


async def _show_services_msg(cq: CallbackQuery, state: FSMContext, session) -> None:
    await cq.answer()
    await _show_services(cq, state, session)


@router.callback_query(SvcCb.filter(), BookingStates.choosing_service)
async def on_service_selected(cq: CallbackQuery, callback_data: SvcCb, state: FSMContext, session) -> None:
    await cq.answer()
    svc_id = callback_data.id
    await state.update_data(service_id=svc_id)
    await state.set_state(BookingStates.choosing_date)
    from datetime import date
    await cq.message.edit_text("Выберите дату:", reply_markup=date_picker(date.today()))


@router.callback_query(DateCb.filter(), BookingStates.choosing_date)
async def on_date_selected(cq: CallbackQuery, callback_data: DateCb, state: FSMContext, session) -> None:
    from datetime import date
    await cq.answer()
    dt_str = callback_data.dt
    d = date.fromisoformat(dt_str)
    await state.update_data(booking_date=dt_str)

    data = await state.get_data()
    org = await OrganizationRepo.get_by_id(session, data["org_id"])
    tz = org.timezone if org else "Asia/Tashkent"

    svc = await ServiceRepo.get_by_id(session, data["service_id"])
    if not svc:
        await cq.message.edit_text("Услуга не найдена.")
        await state.clear()
        return

    bs = BookingService(session)
    slots = await bs.get_available_slots(data["org_id"], data["service_id"], d, tz)
    if not slots:
        await cq.message.edit_text("На эту дату нет свободных слотов.")
        return

    slot_buttons = [(s.timestamp(), s.strftime("%H:%M")) for s in slots]
    await state.set_state(BookingStates.choosing_slot)
    await cq.message.edit_text("Выберите время:", reply_markup=slot_list(slot_buttons))


@router.callback_query(SlotCb.filter(), BookingStates.choosing_slot)
async def on_slot_selected(cq: CallbackQuery, callback_data: SlotCb, state: FSMContext, session) -> None:
    from zoneinfo import ZoneInfo
    await cq.answer()
    ts = float(callback_data.ts)
    data = await state.get_data()
    org = await OrganizationRepo.get_by_id(session, data["org_id"])
    tz = ZoneInfo(org.timezone if org else "Asia/Tashkent")
    slot_dt = datetime.fromtimestamp(ts, tz=tz)
    await state.update_data(slot_ts=ts, slot_tz=org.timezone if org else "Asia/Tashkent")
    await state.set_state(BookingStates.entering_name)
    await cq.message.edit_text("Введите ваше имя (2–100 символов):")


@router.message(BookingStates.entering_name, F.text)
async def on_name_entered(message: Message, state: FSMContext) -> None:
    name = validate_name(message.text or "")
    if not name:
        await message.answer("Имя должно быть от 2 до 100 символов. Попробуйте снова:")
        return
    await state.update_data(client_name=name)
    await state.set_state(BookingStates.entering_phone)
    await message.answer("Введите номер телефона (необязательно, или /skip):")


@router.message(BookingStates.entering_phone, F.text)
async def on_phone_entered(message: Message, state: FSMContext, session) -> None:
    if message.text and message.text.strip() == "/skip":
        phone = None
    else:
        phone = validate_phone(message.text or "") if message.text else None
    await state.update_data(client_phone=phone)

    data = await state.get_data()
    org = await OrganizationRepo.get_by_id(session, data["org_id"])
    tz = org.timezone if org else "Asia/Tashkent"
    slot_dt = datetime.fromtimestamp(data["slot_ts"], tz=ZoneInfo(tz))
    svc = await ServiceRepo.get_by_id(session, data["service_id"])

    summary = (
        f"📋 Подтвердите бронирование:\n\n"
        f"Организация: {org.name if org else '—'}\n"
        f"Услуга: {svc.name if svc else '—'}\n"
        f"Дата и время: {slot_dt.strftime('%d.%m.%Y %H:%M')}\n"
        f"Имя: {data['client_name']}\n"
        f"Телефон: {phone or '—'}\n\n"
        f"Создать заявку?"
    )
    await state.set_state(BookingStates.confirming)
    from app.keyboards.inline import BookingCb, InlineKeyboardButton, InlineKeyboardMarkup
    await message.answer(
        summary,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Создать", callback_data=BookingCb(id="0", action="confirm").pack()),
                InlineKeyboardButton(text="❌ Отмена", callback_data=BookingCb(id="0", action="cancel").pack()),
            ]
        ]),
    )


@router.callback_query(BookingCb.filter(F.action == "confirm"), BookingStates.confirming)
async def on_booking_confirm(cq: CallbackQuery, state: FSMContext, session) -> None:
    from zoneinfo import ZoneInfo
    from app.db.repo import OrganizationAdminRepo
    from aiogram import Bot

    await cq.answer()
    data = await state.get_data()
    org = await OrganizationRepo.get_by_id(session, data["org_id"])
    tz = org.timezone if org else "Asia/Tashkent"
    slot_dt = datetime.fromtimestamp(data["slot_ts"], tz=ZoneInfo(tz))
    user_id = cq.from_user.id if cq.from_user else 0

    bs = BookingService(session)
    booking = await bs.create_booking(
        organization_id=data["org_id"],
        service_id=data["service_id"],
        client_user_id=user_id,
        slot_start=slot_dt,
        client_name=data["client_name"],
        client_phone=data.get("client_phone"),
    )

    if not booking:
        await cq.message.edit_text("Не удалось создать бронирование. Возможно, слот уже занят или подписка неактивна.")
        await state.clear()
        return

    await cq.message.edit_text("✅ Заявка создана и ожидает подтверждения. Мы уведомим вас о результате.")

    admins = await OrganizationAdminRepo.get_admins(session, data["org_id"])
    bot: Bot = cq.bot
    svc = await ServiceRepo.get_by_id(session, data["service_id"])
    admin_text = (
        f"📥 Новая заявка #{booking.id}\n\n"
        f"Услуга: {svc.name if svc else '—'}\n"
        f"Дата: {slot_dt.strftime('%d.%m.%Y %H:%M')}\n"
        f"Клиент: {data['client_name']}\n"
        f"Телефон: {data.get('client_phone') or '—'}"
    )
    from app.keyboards.inline import admin_booking_actions
    for adm in admins:
        try:
            await bot.send_message(adm.user_id, admin_text, reply_markup=admin_booking_actions(booking.id))
        except Exception as e:
            logger.warning("Failed to notify admin %s: %s", adm.user_id, e)

    await state.clear()


@router.callback_query(BookingCb.filter(F.action == "cancel"), BookingStates.confirming)
async def on_booking_cancel_confirm(cq: CallbackQuery, state: FSMContext) -> None:
    await cq.answer()
    await cq.message.edit_text("Бронирование отменено.")
    await state.clear()


# Мои бронирования
@router.message(F.text == MY_BOOKINGS)
async def my_bookings(message: Message, session) -> None:
    user_id = message.from_user.id if message.from_user else 0
    bookings = await BookingRepo.get_future_by_client(session, user_id)
    if not bookings:
        await message.answer("У вас нет активных бронирований.")
        return

    lines = []
    for b in bookings:
        status_emoji = "⏳" if b.status == "PENDING" else "✅"
        lines.append(f"{status_emoji} #{b.id} — {b.start_dt.strftime('%d.%m %H:%M')} ({b.status})")
    await message.answer("Ваши бронирования:\n\n" + "\n".join(lines))


# Отменить бронирование
@router.message(F.text == CANCEL_BOOKING)
async def cancel_booking_start(message: Message, state: FSMContext, session) -> None:
    user_id = message.from_user.id if message.from_user else 0
    bookings = await BookingRepo.get_future_by_client(session, user_id)
    if not bookings:
        await message.answer("Нет бронирований для отмены.")
        return

    from app.keyboards.inline import client_booking_list
    items = [(str(b.id), "Бронь", b.start_dt.strftime("%d.%m %H:%M")) for b in bookings]
    await state.set_state(CancelBookingStates.choosing_booking)
    await state.update_data(booking_ids=[b.id for b in bookings])
    await message.answer("Выберите бронирование для отмены:", reply_markup=client_booking_list(items))


@router.callback_query(BookingCb.filter(F.action == "cancel"), CancelBookingStates.choosing_booking)
async def on_cancel_booking_selected(cq: CallbackQuery, callback_data: BookingCb, state: FSMContext, session) -> None:
    await cq.answer()
    bid = int(callback_data.id)
    data = await state.get_data()
    if bid not in data.get("booking_ids", []):
        await cq.message.edit_text("Бронирование не найдено.")
        await state.clear()
        return

    bs = BookingService(session)
    ok = await bs.cancel_booking(bid, cq.from_user.id if cq.from_user else 0)
    if ok:
        await cq.message.edit_text("✅ Бронирование отменено.")
    else:
        await cq.message.edit_text("Не удалось отменить.")
    await state.clear()
