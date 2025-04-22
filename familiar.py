# Обновленный файл: familiar.py (с argparse для --debug)
# -*- coding: utf-8 -*-

import argparse # Добавляем импорт argparse

# Импортируем функции из наших модулей
import nlu_processor
import command_dispatcher

# --- Парсинг аргументов командной строки ---
parser = argparse.ArgumentParser(description="Фамильяр - Голосовой помощник (текстовый прототип)")
parser.add_argument(
    '--debug',
    action='store_true', # Если флаг указан, значение будет True, иначе False
    help='Запустить в режиме отладки NLU (только печать распознанных интентов).'
)
args = parser.parse_args()
DEBUG_MODE = args.debug # Сохраняем значение флага

# --- Основной цикл программы ---
if __name__ == "__main__":
    print("="*30)
    print("   Прототип Помощника 'Фамильяр'")
    if DEBUG_MODE:
        print("   --- РЕЖИМ ОТЛАДКИ NLU АКТИВЕН ---")
    print("="*30)
    print("Инициализация...")
    # Инициализация диспетчера происходит при импорте command_dispatcher
    print("Готов к приему команд.")
    print("Введите 'выход' для завершения.")
    print("-" * 30)

    while True:
        try:
            command = input(">>> Введите команду: ")
        except EOFError:
            print("\nЗавершение работы (EOF).")
            break

        if command.lower() in ['выход', 'exit', 'quit']:
            print("Завершение работы по команде пользователя.")
            break
        if not command:
            continue

        print("-" * 30)
        print(f"Получена команда: '{command}'")

        print("Обработка NLU...")
        nlu_response_text = nlu_processor.get_nlu_from_ollama(command)

        if nlu_response_text:
            print("Извлечение JSON из ответа NLU...")
            parsed_nlu = nlu_processor.extract_json_from_response(nlu_response_text)

            if parsed_nlu:
                print("Передача в диспетчер...")
                # --- ИЗМЕНЕНИЕ: Передаем флаг debug_mode ---
                dispatcher_result = command_dispatcher.dispatch_command(parsed_nlu, debug_mode=DEBUG_MODE)
                print(f"[FAMILIAR_MAIN] Результат диспетчера: {dispatcher_result}")
            else:
                print("[FAMILIAR_MAIN] Не удалось извлечь JSON из ответа NLU.")
        else:
             print("[FAMILIAR_MAIN] Не получен ответ от NLU процессора.")

        print("-" * 30)