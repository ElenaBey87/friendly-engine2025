import logging
import os
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler
)

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 🔐 Замените токен и chat_id на актуальные данные
TOKEN = "7834653995:AAELsH-lEvlhg_XnmNTEUH0DhJXlFMUDEB8"  # Лучше использовать переменные окружения
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "5598142824"))  # ← Замените на свой chat_id

# Главное меню
main_menu_keyboard = [
    ["📅 Расписание", "✍ Задать вопрос"],
    ["ℹ Частые вопросы"]
]
main_menu = ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True)
back_keyboard = ReplyKeyboardMarkup([["🏠 Главное меню"]], resize_keyboard=True)

# Состояния
ASK_QUESTION = 1

# Часто задаваемые вопросы
faq_data = {
    "Расписание занятий": "📅 Расписание занятий: https://schedule.kantiana.ru/",
    "Расписани сессии": "📝 Экзамены и зачёты: https://schedule.kantiana.ru/",
    "Ошибка в ведомости": "📌 Обратитесь к преподавателю, куратору, руководителю ОП или делопроизводителю.",
    "Найти преподавателя": "👩‍🏫 Найти преподавателя: https://schedule.kantiana.ru/teachers или по почте kantiana.ru. Также смотрите график консультаций по адресу: Калининград, ул. Невского, 14 В, 2 этаж.",
    "Когда каникулы": "🎉 График каникул: https://kantiana.ru/vikon/sveden/files/zix/Grafiki_uchebnogo_processa_obrazovatelynyx_programm_VO_na_2024-2025_uchebnyi_god_podpisy.pdf",
    "Справка об успеваемости": "📄 Справка об успеваемости: через личный кабинет или в МФЦ (Невского, 14, 1 этаж).",
    "Успеваемость": "📊 Успеваемость: в электронной зачётке в личном кабинете студента.",
    "Порядок отчисления": "❗ Подробнее: https://kantiana.ru/vikon/sveden/files/riq/Polozhenie-o-perevode-vnutri-vuza-otch-i-vosst-27_11_2024.pdf",
    "Доступ в личный кабинет": "🔐 Восстановление доступа в личный кабинет: IT-отдел, Невского, 14, каб. 112."
}

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Привет, {update.effective_user.first_name}! Я бот-помощник студента.\nВыберите пункт из меню:",
        reply_markup=main_menu
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Доступные команды:\n/start — Главное меню\n/faq — Часто задаваемые вопросы\n/raspisanie — Расписание"
    )

async def raspisanie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📅 Расписание занятий: https://schedule.kantiana.ru/")

# Часто задаваемые вопросы
async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(key.capitalize(), callback_data=f"faq:{key}")]
        for key in faq_data
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
# Отправляем только ОДНО сообщение с кнопками
    await update.message.reply_text("Выберите вопрос:", reply_markup=reply_markup)

	# Обработка нажатия на FAQ-кнопку
async def handle_faq_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.split(":")[1]
    response = faq_data.get(key, "Информация временно недоступна.")
    
    # Редактируем сообщение с кнопкой — так работает inline
    await query.edit_message_text(text=response)

   
# Новые состояния
ASK_GROUP_QUESTION, ASK_NAME_QUESTION, ASK_TEXT_QUESTION = range(3)

# Начало диалога — сначала спрашиваем группу
async def ask_question_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📌 Укажите вашу группу:", reply_markup=back_keyboard)
    return ASK_GROUP_QUESTION

# Получение группы, переходим к запросу ФИО
async def ask_question_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["group"] = update.message.text.strip()
    await update.message.reply_text("📝 Введите вашу фамилию, имя, отчество:")
    return ASK_NAME_QUESTION

# Получение ФИО, затем просим задать сам вопрос
async def ask_question_fio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["fio"] = update.message.text.strip()
    await update.message.reply_text("✍ Напишите ваш вопрос. Мы ответим вам как можно скорее:")
    return ASK_TEXT_QUESTION

# Получение текста вопроса и отправка админу
async def receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    question = update.message.text.strip()

    if not question:
        await update.message.reply_text("⚠ Пожалуйста, напишите текст вопроса.")
        return ASK_TEXT_QUESTION

    group = context.user_data.get("group", "—")
    fio = context.user_data.get("fio", "—")

    admin_message = (
        f"📩 Новый вопрос от @{user.username or user.first_name} (ID: {user.id}):\n"
        f"👤 ФИО: {fio}\n"
        f"📚 Группа: {group}\n\n"
        f"❓ Вопрос:\n{question}"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения админу: {e}")

    await update.message.reply_text("✅ Ваш вопрос получен. Мы свяжемся с вами при необходимости.", reply_markup=main_menu)
    return ConversationHandler.END


# Обработка меню
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "📅 Расписание":
        await raspisanie(update, context)
    elif text == "ℹ Частые вопросы":
        await faq(update, context)
    elif text == "✍ Задать вопрос":
        return await ask_question_entry(update, context)
    elif text == "🏠 Главное меню":
        await start(update, context)
    else:
        await update.message.reply_text("🤖 Пожалуйста, выберите команду из меню.")

# Отмена ввода
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Вы отменили ввод. Возврат в меню.", reply_markup=main_menu)
    return ConversationHandler.END

# Инициализация приложения
app = ApplicationBuilder().token(TOKEN).build()

# Обработчики команд
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("faq", faq))
app.add_handler(CommandHandler("raspisanie", raspisanie))
app.add_handler(CallbackQueryHandler(handle_faq_click, pattern="^faq:"))

question_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^(✍ Задать вопрос)$"), ask_question_entry)],
    states={
        ASK_GROUP_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_question_group)],
        ASK_NAME_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_question_fio)],
        ASK_TEXT_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_question)],
    },
    fallbacks=[MessageHandler(filters.Regex("^(🏠 Главное меню)$"), cancel)],
)


# Дополнительные обработчики
app.add_handler(question_handler)
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))

# Запуск бота
if __name__ == "__main__":
    print("Бот запущен...")
    app.run_polling()
