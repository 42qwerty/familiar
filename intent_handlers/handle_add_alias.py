# File: intent_handlers/handle_add_alias.py
# -*- coding: utf-8 -*-

import utils
import shutil # Import shutil to check if command exists here

# --- ВОЗВРАЩАЕМ ВТОРОЙ АРГУМЕНТ 'aliases' ---
def handle(parameters, aliases):
    """
    Handles the 'add_alias' intent.
    Modifies the passed 'aliases' dictionary and saves it to file.

    Args:
        parameters (dict): Dictionary of parameters extracted by NLU.
                           Expected keys: 'entity1', 'entity2'.
        aliases (dict): The dictionary of aliases passed from the dispatcher
                        (this is the global APP_ALIASES, which will be modified).

    Returns:
        str: A message indicating success or failure.
    """
    print(f"[HANDLER_ADD_ALIAS][INFO] Handling 'add_alias' intent with parameters: {parameters}")
    # --- УБИРАЕМ ЗАГРУЗКУ АЛИАСОВ ВНУТРИ ОБРАБОТЧИКА ---
    # current_aliases = utils.load_aliases() # <-- УДАЛИТЬ/ЗАКОММЕНТИРОВАТЬ ЭТУ СТРОКУ
    # print(f"[HANDLER_ADD_ALIAS][DEBUG] Loaded fresh aliases: {current_aliases}")
    # --- КОНЕЦ УДАЛЕНИЯ ---

    entity1 = parameters.get("entity1")
    entity2 = parameters.get("entity2")

    if not entity1 or not entity2:
        print(f"[HANDLER_ADD_ALIAS][ERROR] Missing entity1 ('{entity1}') or entity2 ('{entity2}') parameter.")
        return "Не могу добавить псевдоним. Пожалуйста, укажите два имени для связи (например, 'свяжи браузер и google-chrome')."

    entity1_lower = entity1.lower()
    entity2_lower = entity2.lower()

    # Check which entity is the command using shutil.which
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
        msg = f"Ошибка: Оба '{entity1}' и '{entity2}' являются существующими командами."
        print(f"[HANDLER_ADD_ALIAS][ERROR] Both entities are commands: '{entity1}', '{entity2}'.")
        return msg
    else: # Neither is a command
        msg = f"Ошибка: Ни '{entity1}', ни '{entity2}' не являются известными командами в системе."
        print(f"[HANDLER_ADD_ALIAS][ERROR] Neither entity is a command: '{entity1}', '{entity2}'.")
        return msg

    # Если мы правильно определили команду и алиас, вызываем utils.add_alias
    print(f"[HANDLER_ADD_ALIAS][INFO] Proceeding to add alias '{alias_name}' for command '{app_name_command}'.")
    # --- ИСПОЛЬЗУЕМ ПЕРЕДАННЫЙ СЛОВАРЬ 'aliases' ---
    success, message = utils.add_alias(app_name_command, alias_name, aliases) # <-- Используем aliases
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    if success:
        print(f"[HANDLER_ADD_ALIAS][SUCCESS] Alias operation successful for '{alias_name}' -> '{app_name_command}'.")

        # --- СОХРАНЯЕМ ИЗМЕНЕННЫЙ СЛОВАРЬ 'aliases' ---
        save_success, save_message = utils.save_aliases(aliases) # <-- Используем aliases
        # --- КОНЕЦ ИЗМЕНЕНИЯ ---

        if save_success:
            print("[HANDLER_ADD_ALIAS][INFO] Aliases saved successfully to file and updated in memory.")
            # Возвращаем сообщение от add_alias (может быть "добавлен" или "уже существует")
            return message
        else:
            print(f"[HANDLER_ADD_ALIAS][ERROR] Failed to save aliases: {save_message}")
            # Сообщаем, что обновили в памяти, но не смогли сохранить
            return f"{message} (Внимание: псевдоним работает до перезапуска, но не удалось сохранить в файл!)"
    else:
        # Если utils.add_alias вернул False (например, конфликт)
        print(f"[HANDLER_ADD_ALIAS][WARN] Failed to add alias via utils: {message}")
        return message