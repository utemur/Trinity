"""Все тексты RU/UZ."""

TEXTS = {
    "ru": {
        "disclaimer": (
            "⚠️ <b>Дисклеймер:</b> Информация справочная и не является юридической консультацией. "
            "За профессиональной юридической помощью обращайтесь к аккредитованному юристу/адвокату "
            "в Республике Узбекистан."
        ),
        "choose_lang": "Выберите язык / Tilni tanlang:",
        "welcome": "Добро пожаловать в ЮрПомощник Узбекистан!",
        "ask_question": "Введите ваш вопрос (одним сообщением). Не указывайте паспорт, адрес, ИНН, номера карт.",
        "pii_warning": (
            "⚠️ Пожалуйста, не отправляйте персональные данные (паспорт, адрес, ИНН, номера карт). "
            "Переформулируйте вопрос без них."
        ),
        "processing": "Обрабатываю ваш вопрос...",
        "error_api": "Произошла ошибка при обработке. Попробуйте позже.",
        "rate_limit": "Подождите около 20 секунд перед следующим вопросом.",
        "urgent_title": "🆘 Срочный случай — что делать прямо сейчас",
        "urgent_text": (
            "• Сохраняйте спокойствие\n"
            "• Зафиксируйте факты (дата, время, участники)\n"
            "• Не подписывайте документы без консультации\n"
            "• Обратитесь к аккредитованному юристу/адвокату в РУз\n\n"
            "⚠️ За профессиональной помощью — только к юристу."
        ),
        "privacy": (
            "🔒 <b>Конфиденциальность:</b>\n\n"
            "Мы НЕ храним вопросы и ответы. Не собираем персональные данные.\n"
            "Не отправляйте паспорт, адрес, ИНН, номера карт."
        ),
        "help": (
            "ЮрПомощник — справочный бот по законодательству РУз.\n\n"
            "Команды:\n"
            "/start — начать\n"
            "/help — помощь\n"
            "/lang — сменить язык\n"
            "/disclaimer — дисклеймер\n"
            "/privacy — конфиденциальность\n"
            "/about — о боте"
        ),
        "menu_ask": "❓ Задать вопрос",
        "menu_lang": "🌐 Язык",
        "menu_disclaimer": "ℹ️ Дисклеймер",
        "menu_urgent": "🆘 Срочный случай",
        "menu_about": "ℹ️ О боте",
        "menu_label": "Как я могу вам помочь?",
        "about_bot": (
            "<b>О боте Trinity</b>\n\n"
            "Trinity — бот, созданный Усмановым Темуром и является его собственностью.\n\n"
            "Модель обучена помогать пользователям с юридическими вопросами по законодательству "
            "Республики Узбекистан, но не оказывает профессиональную юридическую консультацию.\n\n"
            "Данные предоставляются в режиме реального времени. Бот обучен и обучается на официальных "
            "данных Министерства юстиции Республики Узбекистан."
        ),
    },
    "uz": {
        "disclaimer": (
            "⚠️ <b>Ogohlantirish:</b> Ma'lumot ma'lumotnoma xarakterida va yuridik maslahat emas. "
            "Professional yuridik yordam uchun O'zbekiston Respublikasidagi akkreditatsiyalangan "
            "yurist/advokatga murojaat qiling."
        ),
        "choose_lang": "Tilni tanlang / Выберите язык:",
        "welcome": "YurYordamchi O'zbekiston ga xush kelibsiz!",
        "ask_question": "Savolingizni kiriting (bitta xabar). Pasport, manzil, INN, karta raqamlarini ko'rsatmang.",
        "pii_warning": (
            "⚠️ Iltimos, shaxsiy ma'lumotlarni (pasport, manzil, INN, karta raqamlari) yubormang. "
            "Savolni ularsiz qayta tuzing."
        ),
        "processing": "Savolingizni qayta ishlayapman...",
        "error_api": "Qayta ishlashda xato. Keyinroq urinib ko'ring.",
        "rate_limit": "Keyingi savol oldidan taxminan 20 soniya kuting.",
        "urgent_title": "🆘 Shoshilinch holat — hozir nima qilish kerak",
        "urgent_text": (
            "• Sokin qoling\n"
            "• Faktlarni qayd eting (sana, vaqt, ishtirokchilar)\n"
            "• Maslahatsiz hujjatlarni imzolamang\n"
            "• O'zbekiston Respublikasidagi akkreditatsiyalangan yurist/advokatga murojaat qiling\n\n"
            "⚠️ Professional yordam uchun — faqat yuristga."
        ),
        "privacy": (
            "🔒 <b>Maxfiylik:</b>\n\n"
            "Biz savol va javoblarni SAQLAMAYMIZ. Shaxsiy ma'lumotlarni yig'MAYMIZ.\n"
            "Pasport, manzil, INN, karta raqamlarini yubormang."
        ),
        "help": (
            "YurYordamchi — O'zbekiston Respublikasi qonunchiligi bo'yicha ma'lumotnoma boti.\n\n"
            "Buyruqlar:\n"
            "/start — boshlash\n"
            "/help — yordam\n"
            "/lang — tilni o'zgartirish\n"
            "/disclaimer — ogohlantirish\n"
            "/privacy — maxfiylik\n"
            "/about — bot haqida"
        ),
        "menu_ask": "❓ Savol bering",
        "menu_lang": "🌐 Til",
        "menu_disclaimer": "ℹ️ Ogohlantirish",
        "menu_urgent": "🆘 Shoshilinch holat",
        "menu_about": "ℹ️ Bot haqida",
        "menu_label": "Sizga qanday yordam bera olaman?",
        "about_bot": (
            "<b>Trinity bot haqida</b>\n\n"
            "Trinity — Usmonov Temur tomonidan yaratilgan va uning mulki hisoblanadi.\n\n"
            "Model O'zbekiston Respublikasi qonunchiligi bo'yicha foydalanuvchilarga yuridik savollarda "
            "yordam berish uchun o'qitilgan, lekin professional yuridik maslahat bermaydi.\n\n"
            "Ma'lumotlar real vaqt rejimida taqdim etiladi. Bot O'zbekiston Respublikasi Adliya vazirligi "
            "rasmiy ma'lumotlari asosida o'qitilgan va o'qitilmoqda."
        ),
    },
}
