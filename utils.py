# File: utils.py
# -*- coding: utf-8 -*-

import json
import os
import shutil # To check if alias name is a command

# --- Configuration ---
CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
ALIASES_FILE = os.path.join(CONFIG_DIR, 'app_aliases.json') # Use the correct filename

# --- Alias Management ---

def load_aliases():
    """Loads aliases from the JSON file."""
    print(f"[UTILS_ALIASES][INFO] Attempting to load aliases from: {ALIASES_FILE}")
    os.makedirs(CONFIG_DIR, exist_ok=True)
    try:
        if not os.path.exists(ALIASES_FILE):
            with open(ALIASES_FILE, 'w', encoding='utf-8') as f:
                json.dump({}, f)
            print(f"[UTILS_ALIASES][WARN] Alias file not found. Created empty file: {ALIASES_FILE}")
            return {}
        with open(ALIASES_FILE, 'r', encoding='utf-8') as f:
            aliases = json.load(f)
            if not isinstance(aliases, dict):
                print(f"[UTILS_ALIASES][ERROR] Alias file content is not a valid dictionary. Returning empty.")
                return {}
            print(f"[UTILS_ALIASES][SUCCESS] Aliases loaded ({len(aliases)} found).")
            return {k.lower(): v.lower() for k, v in aliases.items()}
    except json.JSONDecodeError:
        print(f"[UTILS_ALIASES][ERROR] Error decoding JSON from {ALIASES_FILE}. Returning empty.")
        return {}
    except Exception as e:
        print(f"[UTILS_ALIASES][ERROR] Failed to load aliases: {e}")
        return {}

# --- MODIFIED FUNCTION with more DEBUG ---
def save_aliases(aliases):
    """Saves the aliases dictionary to the JSON file."""
    print(f"[UTILS_SAVE][DEBUG] Attempting to save aliases to: {ALIASES_FILE}")
    print(f"[UTILS_SAVE][DEBUG] Aliases to save: {aliases}") # Print the dict being saved
    os.makedirs(CONFIG_DIR, exist_ok=True) # Ensure directory exists
    try:
        print(f"[UTILS_SAVE][DEBUG] Opening file {ALIASES_FILE} for writing...")
        with open(ALIASES_FILE, 'w', encoding='utf-8') as f:
            json.dump(aliases, f, ensure_ascii=False, indent=4, sort_keys=True)
        print(f"[UTILS_SAVE][SUCCESS] Aliases supposedly saved successfully to {ALIASES_FILE}.")
        # Verify file content after saving (for debugging)
        try:
            with open(ALIASES_FILE, 'r', encoding='utf-8') as f_check:
                saved_data = json.load(f_check)
                print(f"[UTILS_SAVE][DEBUG] Verification - Data read back from file: {saved_data}")
        except Exception as e_check:
            print(f"[UTILS_SAVE][ERROR] Verification failed - Could not read back data: {e_check}")

        return True, "Алиасы сохранены."
    except PermissionError as e_perm:
         print(f"[UTILS_SAVE][ERROR] Permission denied when trying to save aliases: {e_perm}")
         return False, f"Ошибка прав доступа при сохранении алиасов: {e_perm}"
    except Exception as e:
        print(f"[UTILS_SAVE][ERROR] Failed to save aliases due to other error: {e}")
        import traceback
        traceback.print_exc() # Print full traceback for unexpected errors
        return False, f"Ошибка при сохранении алиасов: {e}"

# --- REVISED FUNCTION ---
def add_alias(app_name_command, alias_name, aliases_dict):
    """
    Adds a new alias to the dictionary.
    Normalizes names/aliases to lowercase.
    Checks for conflicts. Assumes app_name_command is validated beforehand.
    Allows multiple aliases for the same command.

    Args:
        app_name_command (str): The canonical application command/executable name (validated by handler).
        alias_name (str): The alias to add.
        aliases_dict (dict): The dictionary to add the alias to (will be modified).

    Returns:
        tuple: (bool, str) indicating success and a message.
    """
    app_name_lower = app_name_command.lower()
    alias_name_lower = alias_name.lower()
    print(f"[UTILS_ALIASES][INFO] Attempting to add alias '{alias_name_lower}' for command '{app_name_lower}'.")
    print(f"[UTILS_ALIASES][DEBUG] Current aliases_dict before check: {aliases_dict}")

    is_alias_a_command = shutil.which(alias_name_lower) is not None
    if is_alias_a_command and alias_name_lower != app_name_lower:
        msg = f"Имя '{alias_name}' не может быть псевдонимом, так как это существующая команда в системе."
        print(f"[UTILS_ALIASES][ERROR] {msg}")
        return False, msg

    existing_target = aliases_dict.get(alias_name_lower)
    if existing_target:
        print(f"[UTILS_ALIASES][DEBUG] Found existing alias '{alias_name_lower}' pointing to '{existing_target}'. Comparing with '{app_name_lower}'.")
        if existing_target == app_name_lower:
            msg = f"Псевдоним '{alias_name}' уже существует для команды '{app_name_lower}'. Ничего не изменено."
            print(f"[UTILS_ALIASES][WARN] {msg}")
            return True, msg
        else:
            msg = f"Псевдоним '{alias_name}' уже используется для другой команды ('{existing_target}')."
            print(f"[UTILS_ALIASES][ERROR] {msg}")
            return False, msg

    aliases_dict[alias_name_lower] = app_name_lower
    msg = f"Псевдоним '{alias_name}' успешно добавлен для команды '{app_name_lower}'."
    print(f"[UTILS_ALIASES][SUCCESS] {msg}")
    return True, msg

# --- Other utility functions (if any) can go here ---