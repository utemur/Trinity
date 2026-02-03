"""Обработчики подписки."""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram.types import Message

from app.config import config
from app.db.repo import OrganizationAdminRepo, OrganizationRepo, SubscriptionRepo
from app.keyboards.inline import SubCb, subscription_contact
from app.keyboards.reply import SUBSCRIPTION
from app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)
router = Router(name="subscription")


async def _get_user_org_id(message: Message, session) -> int | None:
    user_id = message.from_user.id if message.from_user else 0
    org_ids = await OrganizationAdminRepo.get_org_ids_for_user(session, user_id)
    if org_ids:
        return org_ids[0]
    if user_id in config.ADMIN_IDS:
        orgs = await OrganizationRepo.get_all(session)
        return orgs[0].id if orgs else None
    return None


@router.message(lambda m: m.text == SUBSCRIPTION)
async def subscription_menu(message: Message, session) -> None:
    org_id = await _get_user_org_id(message, session)
    if not org_id:
        await message.answer("Сначала выберите организацию через /start")
        return

    ps = PaymentService(session)
    status = await ps.get_subscription_status(org_id)
    if not status:
        await message.answer(
            "Подписка не оформлена.\n\n"
            "Для активации обратитесь к администратору или используйте /activate_plan (только для админов).",
            reply_markup=subscription_contact(),
        )
        return

    end = status["current_period_end"]
    if end.tzinfo is None:
        end = end.replace(tzinfo=ZoneInfo("UTC"))
    end_str = end.strftime("%d.%m.%Y")

    if status["is_active"]:
        text = (
            f"💳 Подписка активна\n\n"
            f"План: {status['plan']}\n"
            f"Действует до: {end_str}\n\n"
            "Для продления свяжитесь с нами."
        )
    else:
        text = (
            f"💳 Подписка неактивна\n\n"
            f"План: {status['plan']}\n"
            f"Истекла: {end_str}\n\n"
            "Для возобновления свяжитесь с нами."
        )
    await message.answer(text, reply_markup=subscription_contact())


@router.callback_query(SubCb.filter(F.action == "contact"))
async def on_subscription_contact(cq: CallbackQuery) -> None:
    await cq.answer()
    await cq.message.answer(
        "Для оплаты подписки свяжитесь с администратором бота.\n"
        "Укажите название организации и желаемый план (BASIC/PRO)."
    )


@router.message(Command("activate_plan"))
async def cmd_activate_plan(message: Message, session) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if user_id not in config.ADMIN_IDS:
        await message.answer("Команда только для глобальных администраторов.")
        return

    parts = (message.text or "").split(maxsplit=3)
    if len(parts) < 2:
        await message.answer(
            "Использование: /activate_plan org_id [дней] [план]\n"
            "Пример: /activate_plan 1 30 BASIC"
        )
        return

    try:
        org_id = int(parts[1])
        days = int(parts[2]) if len(parts) > 2 else 30
        plan = (parts[3] or "BASIC").upper() if len(parts) > 3 else "BASIC"
    except (ValueError, IndexError):
        await message.answer("Неверный формат.")
        return

    ps = PaymentService(session)
    sub = await ps.activate_plan_manual(org_id, plan=plan, days=days)
    if sub:
        await message.answer(f"✅ Подписка активирована до {sub.current_period_end.strftime('%d.%m.%Y')}")
    else:
        await message.answer("Организация не найдена.")
