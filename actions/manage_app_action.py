# Файл: actions/manage_app_action.py
# -*- coding: utf-8 -*-

import os
import subprocess
import shutil
import psutil

def run_application(app_path_or_name):
    """Запускает приложение в отдельном процессе."""
    print(f"[ACTION_RUN][INFO] Запуск приложения: '{app_path_or_name}'")
    try:
        if os.name == 'nt':
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            subprocess.Popen([app_path_or_name],
                             creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                             close_fds=True)
        else:
            subprocess.Popen([app_path_or_name], start_new_session=True)
        print(f"[ACTION_RUN][SUCCESS] Команда запуска для '{app_path_or_name}' отправлена.")
        return True
    except FileNotFoundError:
        print(f"[ACTION_RUN][ERROR] Ошибка запуска: Файл или команда '{app_path_or_name}' не найден(а).")
        return False
    except Exception as e:
        print(f"[ACTION_RUN][ERROR] Неизвестная ошибка при запуске '{app_path_or_name}': {e}")
        return False

def find_running_process_pid(app_name_or_path):
    """
    Ищет запущенный процесс по имени или части пути.
    Возвращает PID первого найденного процесса или None.
    """
    if not app_name_or_path:
        return None
    search_term_lower = app_name_or_path.lower()
    base_name = os.path.basename(search_term_lower)
    print(f"[ACTION_FIND][DEBUG] Поиск запущенного процесса для: '{search_term_lower}' (base_name: '{base_name}')")

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'exe']):
        try:
            proc_info = proc.info
            # Проверки по имени, cmdline, exe (как были раньше)
            if proc_info['name'] and base_name in proc_info['name'].lower():
                print(f"[ACTION_FIND][DEBUG] Найден по имени процесса: PID={proc_info['pid']}, Name={proc_info['name']}")
                return proc_info['pid']
            if proc_info['cmdline'] and any(search_term_lower in part.lower() for part in proc_info['cmdline']):
                print(f"[ACTION_FIND][DEBUG] Найден по командной строке: PID={proc_info['pid']}, Cmdline={' '.join(proc_info['cmdline'])}")
                return proc_info['pid']
            if proc_info['exe'] and search_term_lower in proc_info['exe'].lower():
                print(f"[ACTION_FIND][DEBUG] Найден по пути к exe: PID={proc_info['pid']}, Exe={proc_info['exe']}")
                return proc_info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception:
            continue
    print(f"[ACTION_FIND][DEBUG] Запущенный процесс для '{app_name_or_path}' не найден.")
    return None

def activate_window_by_class(window_class_or_name):
    """
    Пытается активировать окно приложения по WM_CLASS или имени с помощью wmctrl -xa (Linux).
    Возвращает True в случае успеха, False в противном случае.
    """
    if os.name == 'nt':
        print("[ACTION_ACTIVATE][WARN] Активация окна по классу/имени не поддерживается на Windows в текущей реализации.")
        return False

    print(f"[ACTION_ACTIVATE][INFO] Попытка активации окна по классу/имени: '{window_class_or_name}' (используя wmctrl)")
    try:
        if not shutil.which('wmctrl'):
             print("[ACTION_ACTIVATE][ERROR] Команда 'wmctrl' не найдена. Установите wmctrl для активации окон.")
             return False
        result = subprocess.run(['wmctrl', '-xa', window_class_or_name],
                                capture_output=True, text=True, check=False, encoding='utf-8')
        if result.returncode == 0:
            print(f"[ACTION_ACTIVATE][SUCCESS] Окно для '{window_class_or_name}' успешно активировано.")
            return True
        else:
            print(f"[ACTION_ACTIVATE][WARN] Не удалось активировать окно для '{window_class_or_name}'. Код возврата wmctrl: {result.returncode}.")
            return False
    except Exception as e:
        print(f"[ACTION_ACTIVATE][ERROR] Неизвестная ошибка при вызове 'wmctrl -xa': {e}")
        return False