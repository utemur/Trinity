"""Обработчик /start и главного меню."""

import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.config import config
from app.db.repo import OrganizationAdminRepo, OrganizationRepo
from app.keyboards.inline import org_list
from app.keyboards.reply import main_menu

logger = logging.getLogger(__name__)
router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session) -> None:
    user_id = message.from_user.id if message.from_user else 0
    is_global_admin = user_id in config.ADMIN_IDS

    orgs = await OrganizationRepo.get_all(session)
    if not orgs:
        if is_global_admin:
            await message.answer(
                "👋 Добро пожаловать! Вы — администратор.\n\n"
                "Организаций пока нет. Создайте первую командой:\n"
                "/create_org Название организации"
            )
        else:
            await message.answer(
                "👋 Добро пожаловать!\n\n"
                "Пока нет доступных организаций для бронирования. Обратитесь к администратору."
            )
        await message.answer("Меню:", reply_markup=main_menu())
        return

    if is_global_admin:
        admin_org_ids = await OrganizationAdminRepo.get_org_ids_for_user(session, user_id)
        if not admin_org_ids:
            await message.answer(
                "👋 Добро пожаловать! Вы — администратор.\n\n"
                "Выберите организацию для управления или создайте новую:\n"
                "/create_org Название"
            )
        else:
            await message.answer("Выберите организацию для управления:")

        org_choices = [(o.id, o.name) for o in orgs]
        await message.answer("Организации:", reply_markup=org_list(org_choices))
    else:
        from app.utils.fsm import BookingStates
        await state.set_state(BookingStates.choosing_org)
        await message.answer("👋 Добро пожаловать! Выберите организацию для бронирования:")
        org_choices = [(o.id, o.name) for o in orgs]
        await message.answer("Организации:", reply_markup=org_list(org_choices))

    await message.answer("Меню:", reply_markup=main_menu())


@router.message(F.text == "⚙️ Настройки")
async def settings_menu(message: Message, session) -> None:
    from app.db.repo import OrganizationAdminRepo
    user_id = message.from_user.id if message.from_user else 0
    org_ids = await OrganizationAdminRepo.get_org_ids_for_user(session, user_id)
    if org_ids or user_id in config.ADMIN_IDS:
        await message.answer("Настройки:\n\n/admin — панель администратора")
    else:
        await message.answer("Настройки:\n\nЗдесь вы можете изменить время уведомлений (скоро).")


@router.message(Command("create_org"))
async def cmd_create_org(message: Message, session) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if user_id not in config.ADMIN_IDS:
        await message.answer("Недостаточно прав.")
        return

    args = message.text.split(maxsplit=1) if message.text else []
    name = args[1].strip() if len(args) > 1 else None
    if not name:
        await message.answer("Использование: /create_org Название организации")
        return

    org = await OrganizationRepo.create(session, name=name, timezone=config.TIMEZONE)
    await OrganizationAdminRepo.add(session, org.id, user_id)
    await message.answer(f"✅ Организация «{name}» создана. Вы назначены администратором.")
    await message.answer("Меню:", reply_markup=main_menu())
