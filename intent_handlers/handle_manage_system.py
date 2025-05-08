# File: intent_handlers/handle_manage_system.py
# -*- coding: utf-8 -*-

from actions import manage_system_action # Используем относительный импорт

def handle(parameters: dict, aliases: dict) -> dict:
    """
    Обрабатывает интент manage_system: вызывает соответствующее действие
    и возвращает СТРУКТУРИРОВАННЫЙ СЛОВАРЬ с результатом.

    Args:
        parameters (dict): Словарь с параметрами от NLU (должен содержать 'action').
        aliases (dict): Словарь с алиасами (здесь не используется, но принимается для унификации).

    Returns:
        dict: Структурированный словарь с результатом операции.
    """
    action = parameters.get("action")
    intent_name = "manage_system" # Имя текущего интента для ответа

    print(f"[HANDLER_SYS][INFO] Handling '{intent_name}' with action: '{action}'")

    if not action:
        print(f"[HANDLER_SYS][ERROR] Missing 'action' in parameters for intent '{intent_name}'.")
        return {
            "status": "error",
            "intent": intent_name,
            "action_performed": "unknown", # Действие не определено
            "message_code": "ERROR_ACTION_MISSING",
            "user_message_hint": "Не указано действие системы",
            "error_details": {"type": "ParameterMissing", "message": "Action parameter is missing"}
        }

    # Переменные для результата
    status_result = "error" # По умолчанию считаем, что будет ошибка
    message_code_result = f"ERROR_UNKNOWN_SYSTEM_ACTION" # Общий код ошибки для неизвестного действия
    user_message_hint_result = f"Неизвестное действие системы: '{action}'"
    data_result = {}
    error_details_result = {"type": "UnknownAction", "message": f"Action '{action}' is not defined for intent '{intent_name}'"}

    action_success = False # Флаг успеха выполнения действия из action-модуля
    action_message = ""    # Сообщение от action-модуля

    if action == "shutdown":
        print("[HANDLER_SYS][WARN] Initiating system shutdown.")
        action_success, action_message = manage_system_action.system_shutdown()
        if action_success:
            status_result = "success"
            message_code_result = "SYSTEM_SHUTDOWN_INITIATED"
            user_message_hint_result = "Выключение системы инициировано"
            error_details_result = {} # Очищаем детали ошибки при успехе
        else:
            message_code_result = "ERROR_SYSTEM_SHUTDOWN_FAILED"
            user_message_hint_result = "Не удалось инициировать выключение"
            error_details_result = {"type": "ShutdownFailed", "message": action_message}

    elif action == "reboot":
        print("[HANDLER_SYS][WARN] Initiating system reboot.")
        action_success, action_message = manage_system_action.system_reboot()
        if action_success:
            status_result = "success"
            message_code_result = "SYSTEM_REBOOT_INITIATED"
            user_message_hint_result = "Перезагрузка системы инициирована"
            error_details_result = {}
        else:
            message_code_result = "ERROR_SYSTEM_REBOOT_FAILED"
            user_message_hint_result = "Не удалось инициировать перезагрузку"
            error_details_result = {"type": "RebootFailed", "message": action_message}

    elif action == "update":
        print("[HANDLER_SYS][INFO] Initiating system update process.")
        action_success, action_message = manage_system_action.system_update()
        if action_success:
            status_result = "success"
            message_code_result = "SYSTEM_UPDATE_COMPLETED" # Или INITIATED, если процесс долгий и мы не ждем
            user_message_hint_result = "Обновление системы завершено" # Или "запущено"
            # action_message от system_update уже содержит подходящее сообщение
            data_result = {"update_status_message": action_message}
            error_details_result = {}
        else:
            message_code_result = "ERROR_SYSTEM_UPDATE_FAILED"
            user_message_hint_result = "Ошибка при обновлении системы"
            error_details_result = {"type": "UpdateFailed", "message": action_message}
            data_result = {"update_status_message": action_message} # Можно передать сообщение об ошибке

    elif action == "uptime":
        print("[HANDLER_SYS][INFO] Getting system uptime.")
        action_success, action_message = manage_system_action.get_uptime()
        if action_success:
            status_result = "success"
            message_code_result = "SYSTEM_UPTIME_PROVIDED"
            user_message_hint_result = "Время работы системы"
            data_result = {"uptime_string": action_message} # action_message содержит вывод uptime
            error_details_result = {}
        else:
            message_code_result = "ERROR_SYSTEM_UPTIME_FAILED" # Более специфичный код ошибки
            user_message_hint_result = "Не удалось получить время работы"
            error_details_result = {"type": "UptimeCommandFailed", "message": action_message}
            data_result = {"command_output_error": action_message}

    else:
        # Это условие уже обработано значениями по умолчанию, но для ясности:
        print(f"[HANDLER_SYS][ERROR] Unknown action '{action}' for intent '{intent_name}'.")
        # status_result, message_code_result, user_message_hint_result, error_details_result
        # уже содержат информацию о неизвестном действии.

    # Формируем финальный структурированный ответ
    final_structured_response = {
        "status": status_result,
        "intent": intent_name,
        "action_performed": action,
        "message_code": message_code_result,
        "user_message_hint": user_message_hint_result,
        "data": data_result,
        "error_details": error_details_result if status_result == "error" else {} # Отправляем детали только при ошибке
    }

    print(f"[HANDLER_SYS][DEBUG] Returning structured response: {final_structured_response}")
    return final_structured_response