# File: intent_handlers/handle_add_alias.py
# -*- coding: utf-8 -*-

import utils
import shutil # Для shutil.which

# Список стоп-слов для алиасов (можно вынести в utils или config, если будет расти)
INVALID_ALIAS_WORDS = {'сохрани', 'запомни', 'свяжи', 'пусть', 'себе', 'у', 'это', 'для', 'будет', 'на', 'мне'}

def handle(parameters: dict, aliases: dict) -> dict:
    """
    Обрабатывает интент add_alias: добавляет псевдоним для приложения
    и возвращает СТРУКТУРИРОВАННЫЙ СЛОВАРЬ с результатом.

    Args:
        parameters (dict): Словарь с параметрами от NLU (ожидаются 'entity1', 'entity2').
        aliases (dict): Словарь с алиасами приложений (будет модифицирован).

    Returns:
        dict: Структурированный словарь с результатом операции.
    """
    intent_name = "add_alias"
    action_performed = "add_alias" # В данном случае действие совпадает с интентом

    print(f"[HANDLER_ADD_ALIAS][INFO] Handling '{intent_name}' with parameters: {parameters}")

    entity1 = parameters.get("entity1")
    entity2 = parameters.get("entity2")

    if not entity1 or not entity2:
        print(f"[HANDLER_ADD_ALIAS][ERROR] Missing entity1 ('{entity1}') or entity2 ('{entity2}') in parameters.")
        return {
            "status": "error",
            "intent": intent_name,
            "action_performed": action_performed,
            "message_code": "ERROR_ALIAS_PARAMS_MISSING",
            "user_message_hint": "Не указаны оба имени для создания псевдонима",
            "data": {"entity1": entity1 or "не указано", "entity2": entity2 or "не указано"},
            "error_details": {"type": "ParameterMissing", "message": "entity1 or entity2 parameter is missing"}
        }

    entity1_lower = entity1.lower()
    entity2_lower = entity2.lower()

    # Определяем, что является командой, а что псевдонимом
    entity1_is_command = shutil.which(entity1_lower) is not None
    entity2_is_command = shutil.which(entity2_lower) is not None

    app_name_command = None
    alias_name = None

    if entity1_is_command and not entity2_is_command:
        app_name_command = entity1_lower
        alias_name = entity2_lower
    elif not entity1_is_command and entity2_is_command:
        app_name_command = entity2_lower
        alias_name = entity1_lower
    elif entity1_is_command and entity2_is_command:
        msg = f"Оба '{entity1}' и '{entity2}' являются командами."
        print(f"[HANDLER_ADD_ALIAS][ERROR] Both entities are commands: '{entity1}', '{entity2}'.")
        return {
            "status": "error", "intent": intent_name, "action_performed": action_performed,
            "message_code": "ERROR_ALIAS_BOTH_ARE_COMMANDS",
            "user_message_hint": "Оба указанных имени являются командами",
            "data": {"entity1": entity1, "entity2": entity2},
            "error_details": {"type": "InvalidAliasLogic", "message": msg}
        }
    else: # Ни одна из сущностей не является известной командой
        msg = f"Ни '{entity1}', ни '{entity2}' не являются известными командами."
        print(f"[HANDLER_ADD_ALIAS][ERROR] Neither entity is a command: '{entity1}', '{entity2}'.")
        return {
            "status": "error", "intent": intent_name, "action_performed": action_performed,
            "message_code": "ERROR_ALIAS_NEITHER_IS_COMMAND",
            "user_message_hint": "Ни одно из указанных имен не является командой",
            "data": {"entity1": entity1, "entity2": entity2},
            "error_details": {"type": "InvalidAliasLogic", "message": msg}
        }

    # Проверка псевдонима на стоп-слова
    if alias_name in INVALID_ALIAS_WORDS:
        msg = f"Слово '{alias_name}' не может быть псевдонимом."
        print(f"[HANDLER_ADD_ALIAS][ERROR] Alias name '{alias_name}' is in the invalid list.")
        return {
            "status": "error", "intent": intent_name, "action_performed": action_performed,
            "message_code": "ERROR_ALIAS_INVALID_WORD",
            "user_message_hint": f"Слово '{alias_name}' не подходит для псевдонима",
            "data": {"alias_name": alias_name, "command_name": app_name_command},
            "error_details": {"type": "InvalidAliasName", "message": msg}
        }

    print(f"[HANDLER_ADD_ALIAS][INFO] Attempting to add alias '{alias_name}' for command '{app_name_command}'.")
    
    # Вызов utils.add_alias для добавления/проверки псевдонима в словаре aliases
    # utils.add_alias(app_name_command, alias_name, aliases_dict_to_modify)
    # Возвращает (bool success, str message_from_util)
    add_success, util_message = utils.add_alias(app_name_command, alias_name, aliases)

    if not add_success:
        # utils.add_alias вернул ошибку (например, конфликт, где псевдоним уже используется для ДРУГОЙ команды)
        print(f"[HANDLER_ADD_ALIAS][WARN] Failed to add alias via utils: {util_message}")
        return {
            "status": "error", "intent": intent_name, "action_performed": action_performed,
            "message_code": "ERROR_ALIAS_UTIL_ADD_FAILED", # Общий код, конкретика в util_message
            "user_message_hint": util_message, # Сообщение от utils.add_alias
            "data": {"alias_name": alias_name, "command_name": app_name_command},
            "error_details": {"type": "AliasAddConflictOrError", "message": util_message}
        }

    # Если add_success == True, значит псевдоним либо добавлен, либо уже существовал для ЭТОЙ ЖЕ команды.
    # util_message содержит информацию об этом ("добавлен" или "уже существует")
    
    print(f"[HANDLER_ADD_ALIAS][INFO] Alias operation in memory successful: {util_message}")

    # Сохраняем измененный словарь aliases в файл
    save_success, save_message = utils.save_aliases(aliases)

    if save_success:
        print("[HANDLER_ADD_ALIAS][INFO] Aliases saved successfully to file and updated in memory.")
        # Определяем message_code в зависимости от того, был ли алиас новым или уже существовал
        final_message_code = "ALIAS_ADDED_SUCCESS"
        final_user_hint = f"Псевдоним '{alias_name}' для '{app_name_command}' добавлен"
        if "уже существует" in util_message.lower(): # Проверяем сообщение от utils.add_alias
            final_message_code = "ALIAS_EXISTED_SAME_COMMAND"
            final_user_hint = f"Псевдоним '{alias_name}' для '{app_name_command}' уже был"
        
        return {
            "status": "success", "intent": intent_name, "action_performed": action_performed,
            "message_code": final_message_code,
            "user_message_hint": final_user_hint,
            "data": {"alias_name": alias_name, "command_name": app_name_command}
        }
    else:
        # Ошибка сохранения, но в памяти алиас обновлен/подтвержден
        print(f"[HANDLER_ADD_ALIAS][ERROR] Failed to save aliases to file: {save_message}")
        return {
            "status": "error", "intent": intent_name, "action_performed": action_performed,
            "message_code": "ERROR_ALIAS_SAVE_FAILED",
            "user_message_hint": f"Псевдоним '{alias_name}' для '{app_name_command}' обновлен в памяти, но не сохранен в файл",
            "data": {"alias_name": alias_name, "command_name": app_name_command},
            "error_details": {"type": "FileSaveError", "message": save_message}
        }
