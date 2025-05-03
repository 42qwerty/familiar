# File: intent_handlers/handle_manage_system.py
# -*- coding: utf-8 -*-

# Используем относительный импорт для доступа к соседней папке actions
from actions import manage_system_action

def handle(parameters, aliases):
    """
    Обрабатывает интент manage_system: вызывает соответствующее действие.
    parameters: Словарь с параметрами от NLU (должен содержать 'action').
    aliases: Словарь с алиасами (здесь не используется, но принимается для унификации).
    Возвращает строку с результатом для пользователя.
    """
    action = parameters.get("action")
    print(f"[HANDLER_SYS][INFO] Handling 'manage_system' with action: '{action}'")

    if not action:
        print("[HANDLER_SYS][ERROR] Отсутствует 'action' в параметрах.")
        return "Не поняла, что именно сделать с системой."

    success = False
    message = f"Неизвестное действие системы: '{action}'."

    if action == "shutdown":
        # Добавим предупреждение пользователю
        print("[HANDLER_SYS][WARN] Initiating system shutdown.")
        # Не возвращаем результат _run_command сразу, т.к. ответ может не успеть отправиться
        success, _ = manage_system_action.system_shutdown()
        if success: message = "Инициировано выключение системы..."
        else: message = "Не удалось инициировать выключение." # Сообщение об ошибке уже в логе
    elif action == "reboot":
        print("[HANDLER_SYS][WARN] Initiating system reboot.")
        success, _ = manage_system_action.system_reboot()
        if success: message = "Инициирована перезагрузка системы..."
        else: message = "Не удалось инициировать перезагрузку."
    elif action == "update":
        print("[HANDLER_SYS][INFO] Initiating system update check.")
        success, message = manage_system_action.system_update()
        # Здесь возвращаем сообщение от команды (успех или ошибка apt)
    elif action == "uptime":
        print("[HANDLER_SYS][INFO] Getting system uptime.")
        success, message = manage_system_action.get_uptime()
        # Возвращаем вывод команды uptime или сообщение об ошибке
    else:
        print(f"[HANDLER_SYS][ERROR] Unknown action: {action}")
        # message уже содержит сообщение об ошибке

    print(f"[HANDLER_SYS][INFO] Result for action '{action}': success={success}, message='{message[:100]}...'") # Логируем результат
    return message