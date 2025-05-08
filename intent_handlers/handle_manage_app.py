# File: intent_handlers/handle_manage_app.py
# -*- coding: utf-8 -*-

import shutil # Для shutil.which
import time   # Для time.sleep

# Используем относительный импорт для доступа к соседней папке actions
from actions import manage_app_action
from actions import close_app_action

def handle(parameters: dict, aliases: dict) -> dict:
    """
    Обрабатывает интент manage_app: запускает, фокусирует или закрывает приложение
    и возвращает СТРУКТУРИРОВАННЫЙ СЛОВАРЬ с результатом.
    Использует xdotool для попытки активации из трея/фона.
    Версия 4: Исправлена логика запуска/активации.

    Args:
        parameters (dict): Словарь с параметрами от NLU (должен содержать 'action' и 'app_name').
        aliases (dict): Словарь с алиасами приложений.

    Returns:
        dict: Структурированный словарь с результатом операции.
    """
    action = parameters.get("action")
    app_name_raw = parameters.get("app_name")
    intent_name = "manage_app"

    print(f"[HANDLER_MANAGE_APP][INFO] Handling '{intent_name}' with action: '{action}', app_name_raw: '{app_name_raw}'")

    # --- Базовая проверка параметров ---
    if not action or not app_name_raw:
        print(f"[HANDLER_MANAGE_APP][ERROR] Missing 'action' or 'app_name' in parameters for '{intent_name}'.")
        return {
            "status": "error", "intent": intent_name, "action_performed": action or "unknown",
            "message_code": "ERROR_APP_ACTION_PARAMS_MISSING",
            "user_message_hint": "Не указано действие или имя приложения",
            "data": {"app_name": app_name_raw or "не указано"},
            "error_details": {"type": "ParameterMissing", "message": "Action or app_name parameter is missing"}
        }

    # --- Нормализация имени и подготовка переменных ---
    canonical_name = aliases.get(app_name_raw.lower(), app_name_raw.lower())
    print(f"[HANDLER_MANAGE_APP][INFO] Canonical app name: '{canonical_name}' (raw: '{app_name_raw}')")

    status_result = "error" # По умолчанию
    message_code_result = f"ERROR_UNKNOWN_APP_ACTION"
    user_message_hint_result = f"Неизвестное действие '{action}' для приложения '{canonical_name}'"
    data_result = {"app_name": canonical_name, "app_name_raw": app_name_raw}
    error_details_result = {"type": "UnknownAppAction", "message": f"Action '{action}' is not defined for app '{canonical_name}'"}

    # --- Логика для действия "open" ---
    if action == "open":
        running_pid = manage_app_action.find_running_process_pid(canonical_name)

        if running_pid:
            # --- Сценарий 1: Приложение уже запущено ---
            print(f"[HANDLER_MANAGE_APP][INFO] App '{canonical_name}' is already running (PID: {running_pid}). Attempting to activate...")
            activation_succeeded, activation_code = manage_app_action.activate_window_by_class_or_pid(
                window_class_or_name=canonical_name,
                pid=running_pid
            )

            if activation_succeeded:
                status_result = "success"
                error_details_result = {}
                if activation_code == "WMCTRL_ACTIVATED":
                    message_code_result = "APP_FOCUSED_EXISTING_WMCTRL"
                    user_message_hint_result = f"Окно '{canonical_name}' активировано (wmctrl)"
                elif activation_code == "XDOTOL_ACTIVATED_FROM_PID":
                    message_code_result = "APP_FOCUSED_EXISTING_XDOTOOL"
                    user_message_hint_result = f"Окно '{canonical_name}' активировано (xdotool)"
                else:
                    message_code_result = "APP_FOCUSED_EXISTING_UNKNOWN_METHOD"
                    user_message_hint_result = f"Окно '{canonical_name}' активировано"
            else:
                # Ошибка активации, но приложение запущено
                status_result = "error" # Считаем ошибкой, так как цель "активировать" не достигнута
                error_type = "ActivationFailedUnknown"
                if activation_code == "XDOTOL_NOT_FOUND":
                    message_code_result = "ERROR_APP_ACTIVATE_XDOTOOL_MISSING"
                    user_message_hint_result = f"Не удалось активировать '{canonical_name}': xdotool не установлен"
                    error_type = "XdotoolMissing"
                elif activation_code == "XDOTOL_WINDOW_NOT_FOUND_BY_PID":
                    message_code_result = "ERROR_APP_ACTIVATE_XDOTOOL_NO_WINDOW"
                    user_message_hint_result = f"Приложение '{canonical_name}' запущено, но его окно не найдено (даже xdotool)"
                    error_type = "XdotoolWindowNotFound"
                elif activation_code == "XDOTOL_ACTIVATE_FAILED":
                     message_code_result = "ERROR_APP_ACTIVATE_XDOTOOL_FAILED"
                     user_message_hint_result = f"Не удалось активировать окно '{canonical_name}' с помощью xdotool"
                     error_type = "XdotoolActivateFailed"
                else: # Общая ошибка активации
                    message_code_result = "ERROR_APP_ACTIVATE_FAILED_GENERAL"
                    user_message_hint_result = f"Приложение '{canonical_name}' запущено, но не удалось активировать окно"
                    error_type = "ActivationFailedGeneral"
                error_details_result = {"type": error_type, "message": f"Activation failed with code: {activation_code}"}
        else:
            # --- Сценарий 2: Приложение НЕ запущено ---
            print(f"[HANDLER_MANAGE_APP][INFO] App '{canonical_name}' not found running. Attempting to launch...")
            executable_path = shutil.which(canonical_name)
            if executable_path:
                print(f"[HANDLER_MANAGE_APP][INFO] Found executable: '{executable_path}'. Launching...")
                # --- ИЗМЕНЕНИЕ: Просто запускаем, НЕ пытаемся активировать сразу ---
                launch_success = manage_app_action.run_application(executable_path)
                if launch_success:
                    status_result = "success"
                    message_code_result = "APP_LAUNCHED_SUCCESSFULLY" # Новый код
                    user_message_hint_result = f"Приложение '{canonical_name}' запущено"
                    error_details_result = {}
                else:
                    # Ошибка запуска самого приложения
                    status_result = "error"
                    message_code_result = "ERROR_APP_START_FAILED"
                    user_message_hint_result = f"Не удалось запустить '{canonical_name}'"
                    error_details_result = {"type": "StartFailed", "message": f"manage_app_action.run_application failed for {executable_path}"}
                # --- КОНЕЦ ИЗМЕНЕНИЯ ---
            else:
                # Приложение не найдено в системе
                status_result = "error"
                message_code_result = "ERROR_APP_NOT_FOUND_SYSTEM"
                user_message_hint_result = f"Приложение '{canonical_name}' не найдено в системе"
                error_details_result = {"type": "AppNotFoundSystem", "message": f"Executable for '{canonical_name}' not found via shutil.which"}

    # --- Логика для действия "close" ---
    elif action == "close":
        print(f"[HANDLER_MANAGE_APP][INFO] Attempting to close '{canonical_name}'...")
        close_success = close_app_action.close_application_by_name(canonical_name)
        if close_success:
            status_result = "success"
            message_code_result = "APP_CLOSE_COMMAND_SENT"
            user_message_hint_result = f"Попытка закрыть '{canonical_name}' выполнена"
            error_details_result = {}
        else:
            status_result = "error"
            message_code_result = "ERROR_APP_CLOSE_FAILED_ACTIVE"
            user_message_hint_result = f"Не удалось закрыть '{canonical_name}' (возможно, нет прав)"
            error_details_result = {"type": "CloseFailedActive", "message": f"close_app_action.close_application_by_name returned False for {canonical_name}"}

    # --- Обработка неизвестного действия ---
    else:
        print(f"[HANDLER_MANAGE_APP][WARN] Unknown action '{action}' for intent '{intent_name}'.")
        # status_result, message_code_result и т.д. уже содержат информацию об ошибке

    # --- Формирование финального ответа ---
    final_structured_response = {
        "status": status_result,
        "intent": intent_name,
        "action_performed": action,
        "message_code": message_code_result,
        "user_message_hint": user_message_hint_result,
        "data": data_result,
        "error_details": error_details_result if status_result == "error" else {}
    }

    print(f"[HANDLER_MANAGE_APP][DEBUG] Returning structured response: {final_structured_response}")
    return final_structured_response