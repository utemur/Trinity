"""Обработчики админ-панели."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import config
from app.utils.fsm import BookingStates
from app.db.repo import (
    AvailabilityRuleRepo,
    BlackoutDateRepo,
    BookingRepo,
    OrganizationAdminRepo,
    OrganizationRepo,
    ServiceRepo,
)
from app.keyboards.inline import AdminBookingCb, AdminCb, admin_menu, back_to_admin, OrgCb
from app.services.booking_service import BookingService
from app.services.reminder_service import ReminderService

logger = logging.getLogger(__name__)
router = Router(name="admin_booking")


def _is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


async def _is_org_admin(session, org_id: int, user_id: int) -> bool:
    if user_id in config.ADMIN_IDS:
        return True
    return await OrganizationAdminRepo.is_admin(session, org_id, user_id)


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext, session) -> None:
    user_id = message.from_user.id if message.from_user else 0
    await state.clear()

    org_ids = await OrganizationAdminRepo.get_org_ids_for_user(session, user_id)
    if not org_ids and user_id not in config.ADMIN_IDS:
        await message.answer("У вас нет доступа к админ-панели.")
        return

    if user_id in config.ADMIN_IDS and not org_ids:
        orgs = await OrganizationRepo.get_all(session)
        if not orgs:
            await message.answer("Создайте организацию: /create_org Название")
            return
        org_ids = [o.id for o in orgs]

    if len(org_ids) == 1:
        await _show_admin_menu(message, org_ids[0], session)
        return

    from app.keyboards.inline import org_list
    orgs = await OrganizationRepo.get_all(session)
    orgs_filtered = [o for o in orgs if o.id in org_ids]
    await message.answer("Выберите организацию:", reply_markup=org_list([(o.id, o.name) for o in orgs_filtered]))


@router.callback_query(OrgCb.filter(), ~StateFilter(BookingStates.choosing_org))
async def on_admin_org_selected(cq: CallbackQuery, callback_data: OrgCb, session) -> None:
    user_id = cq.from_user.id if cq.from_user else 0
    if user_id not in config.ADMIN_IDS:
        return
    org_id = callback_data.id
    await cq.answer()
    await _show_admin_menu(cq.message, org_id, session)


async def _show_admin_menu(message_or_cq, org_id: int, session) -> None:
    kb = admin_menu(org_id)
    text = "⚙️ Админ-панель"
    if hasattr(message_or_cq, "edit_text"):
        await message_or_cq.edit_text(text, reply_markup=kb)
    else:
        await message_or_cq.answer(text, reply_markup=kb)


@router.callback_query(AdminCb.filter(F.section == "menu"))
async def on_admin_menu(cq: CallbackQuery, callback_data: AdminCb, session) -> None:
    await cq.answer()
    org_id = callback_data.id
    user_id = cq.from_user.id if cq.from_user else 0
    if not await _is_org_admin(session, org_id, user_id):
        await cq.answer("Нет доступа", show_alert=True)
        return
    await _show_admin_menu(cq.message, org_id, session)


@router.callback_query(AdminCb.filter(F.section == "pending"))
async def on_admin_pending(cq: CallbackQuery, callback_data: AdminCb, session) -> None:
    await cq.answer()
    org_id = callback_data.id
    user_id = cq.from_user.id if cq.from_user else 0
    if not await _is_org_admin(session, org_id, user_id):
        await cq.answer("Нет доступа", show_alert=True)
        return

    pending = await BookingRepo.get_pending_by_org(session, org_id)
    if not pending:
        await cq.message.edit_text("Нет ожидающих бронирований.", reply_markup=back_to_admin(org_id))
        return

    from app.keyboards.inline import admin_booking_actions
    from sqlalchemy.orm import selectinload

    lines = []
    for b in pending:
        await cq.message.answer(
            f"📥 #{b.id} — {b.start_dt.strftime('%d.%m %H:%M')} | {b.client_name}",
            reply_markup=admin_booking_actions(b.id),
        )
    await cq.message.edit_text("Ожидающие бронирования (см. выше):", reply_markup=back_to_admin(org_id))


@router.callback_query(AdminBookingCb.filter(F.action.in_(["confirm", "reject"])))
async def on_admin_booking_action(cq: CallbackQuery, callback_data: AdminBookingCb, session) -> None:
    await cq.answer()
    booking_id = callback_data.id
    action = callback_data.action
    user_id = cq.from_user.id if cq.from_user else 0

    booking = await BookingRepo.get_by_id(session, booking_id)
    if not booking:
        await cq.answer("Бронирование не найдено", show_alert=True)
        return

    if not await _is_org_admin(session, booking.organization_id, user_id):
        await cq.answer("Нет доступа", show_alert=True)
        return

    bs = BookingService(session)
    if action == "confirm":
        ok = await bs.confirm_booking(booking_id, booking.organization_id, user_id)
        if ok:
            await cq.message.edit_text(f"✅ Бронирование #{booking_id} подтверждено.")
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            from app.db.models import Booking
            result = await session.execute(
                select(Booking).where(Booking.id == booking_id).options(selectinload(Booking.service))
            )
            b = result.scalar_one_or_none()
            if b:
                rs = ReminderService(session)
                org = await OrganizationRepo.get_by_id(session, booking.organization_id)
                await rs.schedule_for_booking(b, org.timezone if org else "Asia/Tashkent")
            try:
                await cq.bot.send_message(
                    booking.client_user_id,
                    f"✅ Ваше бронирование #{booking_id} подтверждено на {booking.start_dt.strftime('%d.%m.%Y %H:%M')}.",
                )
            except Exception:
                pass
        else:
            await cq.answer("Не удалось подтвердить", show_alert=True)
    else:
        ok = await bs.reject_booking(booking_id, booking.organization_id, user_id)
        if ok:
            await cq.message.edit_text(f"❌ Бронирование #{booking_id} отклонено.")
            try:
                await cq.bot.send_message(
                    booking.client_user_id,
                    f"❌ К сожалению, ваше бронирование #{booking_id} было отклонено.",
                )
            except Exception:
                pass
        else:
            await cq.answer("Не удалось отклонить", show_alert=True)


@router.callback_query(AdminBookingCb.filter(F.action == "reschedule"))
async def on_admin_reschedule(cq: CallbackQuery) -> None:
    await cq.answer("Перенос бронирования — в разработке (TODO)", show_alert=True)


@router.callback_query(AdminCb.filter(F.section == "stats"))
async def on_admin_stats(cq: CallbackQuery, callback_data: AdminCb, session) -> None:
    await cq.answer()
    org_id = callback_data.id
    user_id = cq.from_user.id if cq.from_user else 0
    if not await _is_org_admin(session, org_id, user_id):
        await cq.answer("Нет доступа", show_alert=True)
        return

    stats = await BookingRepo.get_stats(session, org_id, days=7)
    text = (
        f"📊 Статистика за 7 дней:\n\n"
        f"Всего: {stats['total']}\n"
        f"Подтверждено: {stats['confirmed']}\n"
        f"Отменено: {stats['canceled']}\n"
        f"Ожидает: {stats['pending']}"
    )
    await cq.message.edit_text(text, reply_markup=back_to_admin(org_id))


@router.callback_query(AdminCb.filter(F.section == "services"))
async def on_admin_services(cq: CallbackQuery, callback_data: AdminCb, session) -> None:
    await cq.answer()
    org_id = callback_data.id
    user_id = cq.from_user.id if cq.from_user else 0
    if not await _is_org_admin(session, org_id, user_id):
        await cq.answer("Нет доступа", show_alert=True)
        return

    services = await ServiceRepo.get_by_org(session, org_id, active_only=False)
    lines = [f"• {s.name} ({s.duration_minutes} мин) — {'✅' if s.is_active else '❌'}" for s in services]
    text = "📋 Услуги:\n\n" + ("\n".join(lines) if lines else "Нет услуг.\nДобавить: /add_service Название Длительность_мин")
    await cq.message.edit_text(text, reply_markup=back_to_admin(org_id))


@router.message(Command("add_service"))
async def cmd_add_service(message: Message, session) -> None:
    user_id = message.from_user.id if message.from_user else 0
    parts = (message.text or "").split(maxsplit=3)
    if len(parts) < 4:
        await message.answer("Использование: /add_service org_id Название Длительность_мин [цена]")
        return

    try:
        org_id = int(parts[1])
        name = parts[2]
        duration = int(parts[3])
        price = int(parts[4]) if len(parts) > 4 else None
    except (ValueError, IndexError):
        await message.answer("Неверный формат. Пример: /add_service 1 Стрижка 60")
        return

    if not await _is_org_admin(session, org_id, user_id):
        await message.answer("Нет доступа.")
        return

    await ServiceRepo.create(session, org_id, name, duration, price)
    await message.answer(f"✅ Услуга «{name}» добавлена.")


@router.callback_query(AdminCb.filter(F.section == "schedule"))
async def on_admin_schedule(cq: CallbackQuery, callback_data: AdminCb, session) -> None:
    await cq.answer()
    org_id = callback_data.id
    user_id = cq.from_user.id if cq.from_user else 0
    if not await _is_org_admin(session, org_id, user_id):
        await cq.answer("Нет доступа", show_alert=True)
        return

    rules = await AvailabilityRuleRepo.get_by_org(session, org_id)
    weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    lines = [f"• {weekdays[r.weekday]}: {r.start_time.strftime('%H:%M')}-{r.end_time.strftime('%H:%M')} (шаг {r.slot_step_minutes} мин)" for r in rules]
    text = "🕐 Расписание:\n\n" + ("\n".join(lines) if lines else "Нет правил. Добавить: /add_rule org_id weekday start end [step]\nПример: /add_rule 1 0 09:00 18:00 30")
    await cq.message.edit_text(text, reply_markup=back_to_admin(org_id))


@router.message(Command("add_rule"))
async def cmd_add_rule(message: Message, session) -> None:
    user_id = message.from_user.id if message.from_user else 0
    parts = (message.text or "").split(maxsplit=5)
    if len(parts) < 5:
        await message.answer("Использование: /add_rule org_id weekday start end [step]\nПример: /add_rule 1 0 09:00 18:00 30")
        return

    try:
        org_id = int(parts[1])
        weekday = int(parts[2])
        start = parts[3]
        end = parts[4]
        step = int(parts[5]) if len(parts) > 5 else 30
    except (ValueError, IndexError):
        await message.answer("Неверный формат.")
        return

    if not await _is_org_admin(session, org_id, user_id):
        await message.answer("Нет доступа.")
        return

    await AvailabilityRuleRepo.create(session, org_id, weekday, start, end, step)
    await message.answer(f"✅ Правило добавлено: {start}-{end} (день {weekday}).")


@router.callback_query(AdminCb.filter(F.section == "blackout"))
async def on_admin_blackout(cq: CallbackQuery, callback_data: AdminCb, session) -> None:
    await cq.answer()
    org_id = callback_data.id
    user_id = cq.from_user.id if cq.from_user else 0
    if not await _is_org_admin(session, org_id, user_id):
        await cq.answer("Нет доступа", show_alert=True)
        return

    blackouts = await BlackoutDateRepo.get_by_org(session, org_id)
    lines = [f"• {b.start_dt.strftime('%d.%m')}-{b.end_dt.strftime('%d.%m')} {b.reason or ''}" for b in blackouts]
    text = "🚫 Выходные/блокировки:\n\n" + ("\n".join(lines) if lines else "Нет. Добавить: /add_blackout org_id start end [reason]\nПример: /add_blackout 1 2025-12-31 2025-12-31 Новый год")
    await cq.message.edit_text(text, reply_markup=back_to_admin(org_id))


@router.message(Command("ical_link"))
async def cmd_ical_link(message: Message, session) -> None:
    user_id = message.from_user.id if message.from_user else 0
    org_ids = await OrganizationAdminRepo.get_org_ids_for_user(session, user_id)
    if not org_ids and user_id not in config.ADMIN_IDS:
        await message.answer("Нет доступа.")
        return

    parts = (message.text or "").split(maxsplit=1)
    org_id = int(parts[1]) if len(parts) > 1 else (org_ids[0] if org_ids else None)
    if not org_id and user_id in config.ADMIN_IDS:
        orgs = await OrganizationRepo.get_all(session)
        org_id = orgs[0].id if orgs else None

    if not org_id:
        await message.answer("Укажите org_id: /ical_link 1")
        return

    org = await OrganizationRepo.get_by_id(session, org_id)
    if not org or not org.ical_token:
        await message.answer("Организация не найдена.")
        return

    if not await _is_org_admin(session, org_id, user_id):
        await message.answer("Нет доступа.")
        return

    from app.config import config as cfg
    port = cfg.ICAL_SERVER_PORT
    base = cfg.BASE_URL or f"http://localhost:{port}"
    url = f"{base}/ical/{org_id}/{org.ical_token}.ics"
    await message.answer(f"Ссылка для подписки на календарь:\n{url}")


@router.message(Command("add_blackout"))
async def cmd_add_blackout(message: Message, session) -> None:
    user_id = message.from_user.id if message.from_user else 0
    parts = (message.text or "").split(maxsplit=4)
    if len(parts) < 4:
        await message.answer("Использование: /add_blackout org_id start_date end_date [reason]")
        return

    try:
        org_id = int(parts[1])
        from datetime import datetime
        from zoneinfo import ZoneInfo
        org = await OrganizationRepo.get_by_id(session, org_id)
        tz = ZoneInfo(org.timezone if org else "Asia/Tashkent")
        start_dt = datetime.strptime(parts[2], "%Y-%m-%d").replace(hour=0, minute=0, second=0, tzinfo=tz)
        end_dt = datetime.strptime(parts[3], "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=tz)
        reason = parts[4] if len(parts) > 4 else None
    except (ValueError, IndexError) as e:
        await message.answer(f"Неверный формат: {e}")
        return

    if not await _is_org_admin(session, org_id, user_id):
        await message.answer("Нет доступа.")
        return

    await BlackoutDateRepo.create(session, org_id, start_dt, end_dt, reason)
    await message.answer("✅ Выходной день добавлен.")
