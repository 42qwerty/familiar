# File: familiar.py (Ядро/Движок Фамильяра)
# -*- coding: utf-8 -*-

import json
import nlu_processor # Наш обновленный модуль
import command_dispatcher

# --- Шаблон инструкции для NLU (извлечение интента) ---
# Используется функцией nlu_processor.get_nlu_intent_from_text
# NLU_INSTRUCTION_TEMPLATE = nlu_processor.NLU_INSTRUCTION_TEMPLATE # Определен в nlu_processor

# --- Шаблон инструкции для генерации ответа LLM ---
RESPONSE_GENERATION_INSTRUCTION_TEMPLATE = """Тебе будет предоставлен структурированный результат выполнения команды пользователя ассистентом "Фамильяр".
Твоя задача - на основе этих данных сгенерировать естественный, дружелюбный и полезный ответ для пользователя на русском языке.
Ты Фамильяр, вежливый и немногословный помощник.

Структура входных данных:
{{
  "status": "success" | "error",        // Итог операции
  "intent": "имя_интента",              // Исходный интент
  "action_performed": "имя_действия",   // Выполненное действие
  "message_code": "КОД_РЕЗУЛЬТАТА",     // Уникальный код исхода
  "user_message_hint": "Подсказка",    // Краткая подсказка на русском (может отсутствовать)
  "data": {{}},                           // Данные для включения в ответ (могут отсутствовать)
  "error_details": {{ "type": "...", "message": "..."}} // Детали ошибки (только при status="error", могут отсутствовать)
}}

Интерпретируй `message_code` и `data` для формирования ответа.
Если `status` равен "error", сообщи об ошибке вежливо. Не показывай пользователю `error_details.message`.
Если есть `user_message_hint`, он может помочь тебе понять контекст.

Примеры интерпретации `message_code` и `data`:

1.  `message_code`: "APP_OPENED_NEW_FOCUSED", `data`: {{"app_name": "firefox"}}
    Ответ может быть: "Открыл и активировал Firefox для вас." или "Firefox запущен."

2.  `message_code`: "ALIAS_ADDED_SUCCESS", `data`: {{"alias_name": "тг", "command_name": "telegram"}}
    Ответ: "Хорошо, запомнил: 'тг' теперь означает 'telegram'."

3.  `message_code`: "ERROR_APP_NOT_FOUND_SYSTEM", `data`: {{"app_name": "non_existent_app"}}
    Ответ: "Простите, не могу найти приложение 'non_existent_app'. Убедитесь, что оно установлено и имя верное."

4.  `message_code`: "SYSTEM_UPTIME_PROVIDED", `data`: {{"uptime_string": "02:45 up 1 day, 3:12"}}
    Ответ: "Система работает уже 1 день, 3 часа и 12 минут."

5.  `message_code`: "SYSTEM_UPDATE_INITIATED"
    Ответ: "Понял, запускаю обновление системы. Это может занять некоторое время."

6.  `message_code`: "REBOOT_INITIATED"
    Ответ: "Хорошо, инициирую перезагрузку системы. До скорой встречи!"

7.  `message_code`: "ERROR_PERMISSION_SUDO"
    Ответ: "Кажется, у меня недостаточно прав для выполнения этой команды. Возможно, нужно настроить sudo."

Действуй! Вот структурированный результат:
{structured_data_json}
Твой ответ:
"""

def generate_natural_response(structured_result: dict) -> str:
    """
    Отправляет структурированный результат в LLM для генерации ответа.
    """
    print(f"[FAMILIAR_CORE][INFO] Generating natural response for: {structured_result}")
    if not structured_result or not isinstance(structured_result, dict):
        print("[FAMILIAR_CORE][ERROR] Structured result is invalid, cannot generate response.")
        return "Произошла внутренняя ошибка при подготовке ответа."

    try:
        structured_data_json_string = json.dumps(structured_result, ensure_ascii=False, indent=2)
    except TypeError as e:
        print(f"[FAMILIAR_CORE][ERROR] Failed to serialize structured_result to JSON: {e}")
        return "Произошла внутренняя ошибка: не удалось сериализовать результат."

    # Формируем ПОЛНЫЙ текст инструкции для генерации ответа
    instruction_for_response_generation = RESPONSE_GENERATION_INSTRUCTION_TEMPLATE.format(
        structured_data_json=structured_data_json_string
    )

    # Вызываем новую функцию из nlu_processor для генерации ответа
    response_text = nlu_processor.generate_llm_response_from_template(
        full_prompt_text=instruction_for_response_generation
        # model_name, api_url и т.д. будут использоваться по умолчанию из nlu_processor
    )

    if response_text:
        return response_text.strip()
    else:
        print("[FAMILIAR_CORE][ERROR] LLM did not return a response for structured data.")
        # Возвращаем запасной вариант на основе user_message_hint или общего сообщения
        hint = structured_result.get("user_message_hint", "")
        if structured_result.get("status") == "success":
            return hint if hint else "Команда выполнена."
        else:
            return hint if hint else "Произошла ошибка при выполнении команды."


def process_text_command(user_text: str) -> str:
    """
    Полный цикл обработки текстовой команды пользователя.
    1. NLU для извлечения интента и параметров.
    2. Диспетчеризация и выполнение команды.
    3. Генерация естественного ответа на основе результата.
    """
    print(f"[FAMILIAR_CORE][INFO] Processing command: '{user_text}'")

    # 1. NLU (извлечение интента)
    # Используем переименованную функцию nlu_processor.get_nlu_intent_from_text
    nlu_raw_response = nlu_processor.get_nlu_intent_from_text(user_text)
    if not nlu_raw_response:
        print("[FAMILIAR_CORE][ERROR] NLU processor did not return a response.")
        # TODO: Можно сделать вызов generate_natural_response с ошибкой NLU_FAILED
        return "Извините, не удалось связаться с системой распознавания команд."

    parsed_nlu = nlu_processor.extract_json_from_response(nlu_raw_response)
    if not parsed_nlu or "intent" not in parsed_nlu : # Добавил проверку на "intent"
        print(f"[FAMILIAR_CORE][ERROR] Failed to parse JSON from NLU or 'intent' is missing. Raw: '{nlu_raw_response}'")
        # TODO: Можно сделать вызов generate_natural_response с ошибкой NLU_PARSE_FAILED
        return "Простите, я получил не совсем понятный ответ от системы распознавания. Попробуйте перефразировать."

    # 2. Диспетчеризация и выполнение команды
    # dispatch_command теперь возвращает структурированный ответ
    # Передаем APP_ALIASES из command_dispatcher, так как обработчики ожидают его
    structured_result = command_dispatcher.dispatch_command(parsed_nlu, debug_mode=False)

    if not structured_result or not isinstance(structured_result, dict):
        print(f"[FAMILIAR_CORE][ERROR] Dispatcher returned invalid structured result: {structured_result}")
        # TODO: Можно сделать вызов generate_natural_response с ошибкой DISPATCHER_FAILED
        return "Произошла внутренняя ошибка при выполнении вашей команды."

    # 3. Генерация естественного ответа
    final_response = generate_natural_response(structured_result)

    print(f"[FAMILIAR_CORE][INFO] Final response to user: '{final_response}'")
    return final_response


if __name__ == "__main__":
    # Простой тестовый цикл для familiar.py
    print("Фамильяр (консольный интерфейс ядра) v0.3 - Генерация ответов")
    print("Инициализация...")
    # command_dispatcher.initialize_dispatcher() # Вызывается при импорте command_dispatcher
    print("Готов к приему команд. Введите 'выход' для завершения.")
    print("-" * 30)

    while True:
        try:
            command = input(">>> Вы: ")
            if command.lower() in ['выход', 'exit', 'quit']:
                break
            if not command:
                continue

            response = process_text_command(command)
            print(f"Фамильяр: {response}")
            print("-" * 30)
        except EOFError:
            print("\nЗавершение работы.")
            break
        except KeyboardInterrupt:
            print("\nЗавершение работы по Ctrl+C.")
            break
