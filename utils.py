# -*- coding: utf-8 -*-

import json
import os

# --- Константы ---
# Путь к файлу алиасов относительно папки config
ALIASES_FILE_PATH = os.path.join('config', 'app_aliases.json')

def load_aliases(filepath=ALIASES_FILE_PATH):
    """Загружает алиасы из JSON файла."""
    print(f"[DEBUG] Попытка загрузки алиасов из: {filepath}")
    # Используем абсолютный путь от места запуска скрипта,
    # предполагая, что скрипт запускается из корневой папки проекта familiar_project/
    abs_filepath = os.path.abspath(filepath)
    print(f"[DEBUG] Абсолютный путь к файлу алиасов: {abs_filepath}")
    try:
        with open(abs_filepath, 'r', encoding='utf-8') as f:
            aliases = json.load(f)
        # Приводим ключи алиасов к нижнему регистру для удобства поиска
        return {k.lower(): v for k, v in aliases.items()}
    except FileNotFoundError:
        print(f"Предупреждение: Файл алиасов '{abs_filepath}' не найден.")
        return {}
    except json.JSONDecodeError:
        print(f"Ошибка: Не удалось прочитать JSON из файла '{abs_filepath}'. Файл поврежден или пуст?")
        return {}
    except Exception as e:
        print(f"Неизвестная ошибка при загрузке алиасов из '{abs_filepath}': {e}")
        return {}

# Можно добавить здесь другие общие утилиты в будущем