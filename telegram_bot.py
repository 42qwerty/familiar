# File: telegram_bot.py
# -*- coding: utf-8 -*-
import logging
import os

# --- ИМПОРТИРУЕМ НОВОЕ ЯДРО ФАМИЛЬЯРА ---
import familiar # Наш новый основной модуль с process_text_command

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- КОНФИГУРАЦИЯ ---
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    logger.error("Токен Telegram бота не найден! Установите переменную окружения TELEGRAM_BOT_TOKEN.")
    exit()

# --- ОБРАБОТЧИКИ КОМАНД TELEGRAM ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение при команде /start."""
    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.mention_html()}! Я Фамильяр, ваш помощник. Просто напишите мне команду.",
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет сообщение с помощью при команде /help."""
    await update.message.reply_text("Просто отправьте мне команду текстом, например: 'открой браузер' или 'закрой telegram'.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает текстовые сообщения пользователя, передавая их ядру Фамильяра."""
    command_text = update.message.text
    user_id = update.effective_user.id
    logger.info(f"Получена команда от пользователя {user_id}: '{command_text}'")

    # Отправляем предварительное сообщение (можно оставить или убрать)
    # await update.message.reply_text(f"Получил команду: '{command_text}'. Обрабатываю...")

    try:
        # --- ИСПОЛЬЗУЕМ НОВОЕ ЯДРО ДЛЯ ОБРАБОТКИ КОМАНДЫ ---
        # familiar.process_text_command теперь делает всю работу:
        # 1. NLU для извлечения интента
        # 2. Диспетчеризация и выполнение команды (которая вернет структурированный результат)
        # 3. Генерация естественного ответа на основе структурированного результата
        final_response_text = familiar.process_text_command(command_text)
        # --- КОНЕЦ ИЗМЕНЕНИЯ ---

        logger.info(f"Финальный ответ для пользователя: {final_response_text}")
        await update.message.reply_text(final_response_text)

    except Exception as e:
        logger.error(f"Ошибка при вызове familiar.process_text_command: {e}", exc_info=True)
        # В случае серьезной ошибки в ядре, отправляем общее сообщение
        await update.message.reply_text(f"Произошла неожиданная внутренняя ошибка при обработке вашей команды: {e}")


# --- ОСНОВНАЯ ФУНКЦИЯ ЗАПУСКА БОТА ---

def main() -> None:
    """Запускает Telegram бота."""
    # Инициализация диспетчера и других компонентов ядра происходит при импорте
    # familiar.py и command_dispatcher.py
    logger.info("Инициализация ядра Фамильяра (диспетчер и т.д.)...")
    # command_dispatcher.initialize_dispatcher() # Вызывается при импорте command_dispatcher

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Запуск Telegram бота...")
    application.run_polling()

if __name__ == '__main__':
    main()
