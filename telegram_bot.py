# -*- coding: utf-8 -*-
import logging
import os # Для чтения токена из переменной окружения

# Импортируем наши модули Фамильяра
import nlu_processor
import command_dispatcher

# Импортируем необходимые классы из библиотеки python-telegram-bot
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования (полезно для отладки)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- КОНФИГУРАЦИЯ ---
# Получаем токен из переменной окружения (более безопасно)
# Перед запуском установи переменную окружения: export TELEGRAM_BOT_TOKEN='ВАШ_ТОКЕН'
# Или просто вставь токен сюда для теста: TELEGRAM_BOT_TOKEN = 'ВАШ_СУПЕР_СЕКРЕТНЫЙ_ТОКЕН'
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    logger.error("Токен Telegram бота не найден! Установите переменную окружения TELEGRAM_BOT_TOKEN.")
    exit() # Выход, если токен не найден

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
    """Обрабатывает текстовые сообщения пользователя как команды для Фамильяра."""
    command_text = update.message.text
    user_id = update.effective_user.id # Можно использовать для разграничения доступа в будущем
    logger.info(f"Получена команда от пользователя {user_id}: '{command_text}'")

    await update.message.reply_text(f"Получил команду: '{command_text}'. Обрабатываю...")

    # 1. Получаем NLU ответ от Ollama
    logger.info("Обработка NLU...")
    nlu_response_text = nlu_processor.get_nlu_from_ollama(command_text)

    if not nlu_response_text:
        logger.warning("Не получен ответ от NLU процессора.")
        await update.message.reply_text("Не удалось связаться с NLU процессором.")
        return

    # 2. Извлекаем JSON из ответа NLU
    logger.info("Извлечение JSON из ответа NLU...")
    parsed_nlu = nlu_processor.extract_json_from_response(nlu_response_text)

    if not parsed_nlu:
        logger.warning("Не удалось извлечь JSON из ответа NLU.")
        # Отправляем сырой ответ NLU пользователю для отладки (можно убрать потом)
        await update.message.reply_text(f"Не удалось разобрать ответ NLU. Ответ был:\n```\n{nlu_response_text}\n```")
        return

    # 3. Передаем команду в диспетчер Фамильяра (в рабочем режиме!)
    logger.info(f"Передача в диспетчер: {parsed_nlu}")
    try:
        # Вызываем диспетчер из нашего модуля command_dispatcher
        # Передаем False для debug_mode, так как это рабочий режим бота
        dispatcher_result = command_dispatcher.dispatch_command(parsed_nlu, debug_mode=False)
        logger.info(f"Результат диспетчера: {dispatcher_result}")
        # Отправляем результат пользователю
        await update.message.reply_text(str(dispatcher_result)) # Преобразуем результат в строку на всякий случай
    except Exception as e:
        logger.error(f"Ошибка при вызове диспетчера: {e}", exc_info=True)
        await update.message.reply_text(f"Произошла внутренняя ошибка при обработке команды: {e}")


# --- ОСНОВНАЯ ФУНКЦИЯ ЗАПУСКА БОТА ---

def main() -> None:
    """Запускает Telegram бота."""
    # Создаем приложение и передаем ему токен бота.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Регистрируем обработчик для всех текстовых сообщений (кроме команд)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота (он будет работать, пока вы не остановите процесс)
    logger.info("Запуск Telegram бота...")
    application.run_polling()

if __name__ == '__main__':
    main()
