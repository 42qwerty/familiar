# File: actions/manage_app_action.py
# -*- coding: utf-8 -*-

import os
import subprocess
import shutil
import psutil
# import shlex # Пока не нужен

def run_application(app_path_or_name: str) -> bool:
    """Запускает приложение в отдельном процессе."""
    print(f"[ACTION_RUN][INFO] Запуск приложения: '{app_path_or_name}'")
    try:
        if os.name == 'nt': # Для Windows (пока не используется активно)
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            subprocess.Popen([app_path_or_name],
                             creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                             close_fds=True)
        else: # Для Linux/macOS
            # Проверяем, существует ли команда перед запуском
            if not shutil.which(app_path_or_name):
                 print(f"[ACTION_RUN][ERROR] Команда '{app_path_or_name}' не найдена в PATH.")
                 return False
            subprocess.Popen([app_path_or_name], start_new_session=True)
        print(f"[ACTION_RUN][SUCCESS] Команда запуска для '{app_path_or_name}' отправлена.")
        return True
    except FileNotFoundError:
        print(f"[ACTION_RUN][ERROR] Ошибка запуска (FileNotFound): Файл или команда '{app_path_or_name}' не найден(а).")
        return False
    except Exception as e:
        print(f"[ACTION_RUN][ERROR] Неизвестная ошибка при запуске '{app_path_or_name}': {e}")
        return False

# --- ИСПРАВЛЕННАЯ ФУНКЦИЯ ПОИСКА PID (v4 - более гибкий поиск) ---
def find_running_process_pid(app_name_or_path: str) -> int | None:
    """
    Ищет запущенный процесс по имени или части пути.
    Более гибкая проверка имен (например, 'google-chrome' и 'chrome').
    Возвращает PID первого найденного процесса или None.
    """
    if not app_name_or_path:
        return None
    search_term_lower = app_name_or_path.lower()
    base_name_search = os.path.basename(search_term_lower)
    current_pid = os.getpid()

    # --- ИЗМЕНЕНИЕ: Создаем набор возможных имен ---
    possible_names = {base_name_search}
    # Добавляем общие варианты, если ищем специфичные браузеры или приложения
    if base_name_search == "google-chrome" or base_name_search == "google-chrome-stable":
        possible_names.add("chrome")
    elif base_name_search == "firefox" or base_name_search == "firefox-esr":
         possible_names.add("firefox-bin") # Иногда бинарник называется так
    # Добавить другие специфичные варианты по мере необходимости
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    print(f"[ACTION_FIND][DEBUG] Поиск запущенного процесса для: '{search_term_lower}' (возможные имена: {possible_names}), исключая PID: {current_pid}")

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'exe']):
        try:
            proc_info = proc.info
            pid = proc_info.get('pid')

            if pid == current_pid:
                continue

            # --- 1. Проверка по имени процесса (proc.name()) ---
            proc_name_lower = proc_info.get('name', '').lower()
            # --- ИЗМЕНЕНИЕ: Проверяем вхождение в набор имен ---
            if proc_name_lower in possible_names:
                 if not proc_name_lower.startswith('python'): # Исключаем python скрипты
                     print(f"[ACTION_FIND][DEBUG] Найден по имени процесса: PID={pid}, Name={proc_info.get('name')}")
                     return pid
            # --- КОНЕЦ ИЗМЕНЕНИЯ ---

            # --- 2. Проверка по базовому имени исполняемого файла (proc.exe()) ---
            exe_path = proc_info.get('exe')
            if exe_path:
                exe_base_name_lower = os.path.basename(exe_path).lower()
                # --- ИЗМЕНЕНИЕ: Проверяем вхождение в набор имен ---
                if exe_base_name_lower in possible_names:
                     if not exe_base_name_lower.startswith('python'):
                        print(f"[ACTION_FIND][DEBUG] Найден по базовому имени exe: PID={pid}, Exe={exe_path}")
                        return pid
                # --- КОНЕЦ ИЗМЕНЕНИЯ ---

            # --- 3. Проверка по первому аргументу командной строки (proc.cmdline()) ---
            cmdline_list = proc_info.get('cmdline')
            if cmdline_list:
                 first_arg_base_lower = os.path.basename(cmdline_list[0]).lower() if cmdline_list else ''
                 # --- ИЗМЕНЕНИЕ: Проверяем вхождение в набор имен ---
                 if first_arg_base_lower in possible_names:
                      if not first_arg_base_lower.startswith('python'):
                          print(f"[ACTION_FIND][DEBUG] Найден по первому аргументу cmdline: PID={pid}, Cmdline={' '.join(cmdline_list)}")
                          return pid
                 # --- КОНЕЦ ИЗМЕНЕНИЯ ---

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception as e:
             print(f"[ACTION_FIND][WARN] Ошибка при доступе к информации процесса PID {pid}: {e}")
             continue

    print(f"[ACTION_FIND][DEBUG] Запущенный процесс для '{app_name_or_path}' (с учетом {possible_names}) не найден.")
    return None
# --- КОНЕЦ ИСПРАВЛЕННОЙ ФУНКЦИИ ---


def _run_tool_command(command_list: list[str]) -> tuple[bool, str]:
    """Вспомогательная функция для запуска утилит вроде wmctrl или xdotool."""
    tool_name = command_list[0]
    if not shutil.which(tool_name):
        print(f"[ACTION_ACTIVATE][ERROR] Утилита '{tool_name}' не найдена. Установите ее.")
        return False, f"Утилита '{tool_name}' не найдена."
    try:
        print(f"[ACTION_ACTIVATE][DEBUG] Выполнение команды: {' '.join(command_list)}")
        result = subprocess.run(command_list, capture_output=True, text=True, check=False, encoding='utf-8')
        if result.returncode == 0:
            print(f"[ACTION_ACTIVATE][DEBUG] '{tool_name}' выполнено успешно. stdout: {result.stdout.strip()}")
            return True, result.stdout.strip()
        else:
            print(f"[ACTION_ACTIVATE][WARN] '{tool_name}' вернуло ошибку. Код: {result.returncode}. stderr: {result.stderr.strip()}")
            return False, result.stderr.strip()
    except Exception as e:
        print(f"[ACTION_ACTIVATE][ERROR] Ошибка при вызове '{tool_name}': {e}")
        return False, str(e)

def activate_window_by_class_or_pid(window_class_or_name: str, pid: int | None = None) -> tuple[bool, str]:
    """
    Пытается активировать окно приложения.
    Сначала по WM_CLASS или имени с помощью wmctrl.
    Если не удалось и передан PID, пытается найти окно по PID с помощью xdotool и активировать/развернуть его.

    Args:
        window_class_or_name (str): Имя класса окна или имя приложения (для wmctrl и как fallback).
        pid (int | None): PID процесса, окно которого нужно активировать (для xdotool).

    Returns:
        tuple[bool, str]: (успех, код_результата_активации)
    """
    if os.name == 'nt':
        msg = "Активация окна по классу/имени/PID не поддерживается на Windows в текущей реализации."
        print(f"[ACTION_ACTIVATE][WARN] {msg}")
        return False, "UNSUPPORTED_OS"

    # 1. Попытка через wmctrl по имени класса/окна
    print(f"[ACTION_ACTIVATE][INFO] Попытка активации через wmctrl для '{window_class_or_name}'...")
    wmctrl_success, wmctrl_msg = _run_tool_command(['wmctrl', '-xa', window_class_or_name])
    if wmctrl_success:
        print(f"[ACTION_ACTIVATE][SUCCESS] wmctrl успешно активировал окно для '{window_class_or_name}'.")
        return True, "WMCTRL_ACTIVATED" # Возвращаем код успеха

    print(f"[ACTION_ACTIVATE][INFO] wmctrl не смог активировать окно для '{window_class_or_name}' (Сообщение: {wmctrl_msg}).")

    # 2. Если есть PID и wmctrl не справился, пытаемся через xdotool
    if pid:
        print(f"[ACTION_ACTIVATE][INFO] Попытка активации через xdotool для PID {pid} (приложение: '{window_class_or_name}')...")
        if not shutil.which('xdotool'):
            msg = "Утилита 'xdotool' не найдена. Для расширенной активации окон, пожалуйста, установите ее (sudo apt install xdotool)."
            print(f"[ACTION_ACTIVATE][ERROR] {msg}")
            return False, "XDOTOL_NOT_FOUND"

        # Ищем окно по PID
        search_success, window_ids_str = _run_tool_command(['xdotool', 'search', '--pid', str(pid)])
        if not search_success or not window_ids_str:
            msg = f"xdotool не нашел окон для PID {pid} (приложение: '{window_class_or_name}')."
            print(f"[ACTION_ACTIVATE][WARN] {msg}")
            return False, "XDOTOL_WINDOW_NOT_FOUND_BY_PID"

        window_id = window_ids_str.split('\n')[0].strip() # Берем первый ID
        if not window_id:
            msg = f"xdotool вернул пустой ID окна для PID {pid}."
            print(f"[ACTION_ACTIVATE][WARN] {msg}")
            return False, "XDOTOL_EMPTY_WINDOW_ID"

        print(f"[ACTION_ACTIVATE][DEBUG] xdotool нашел ID окна: {window_id} для PID {pid}.")

        # Пытаемся "развернуть/показать" окно (важно для трея)
        map_success, map_msg = _run_tool_command(['xdotool', 'windowmap', window_id])
        if not map_success:
            print(f"[ACTION_ACTIVATE][WARN] xdotool windowmap для ID {window_id} вернул: {map_msg}. Продолжаем с активацией...")

        # Пытаемся активировать окно
        activate_success, activate_msg = _run_tool_command(['xdotool', 'windowactivate', window_id])
        if activate_success:
            print(f"[ACTION_ACTIVATE][SUCCESS] xdotool успешно активировал окно ID {window_id} (PID {pid}).")
            return True, "XDOTOL_ACTIVATED_FROM_PID"
        else:
            msg = f"xdotool не смог активировать окно ID {window_id} (PID {pid}). Сообщение: {activate_msg}"
            print(f"[ACTION_ACTIVATE][WARN] {msg}")
            return False, "XDOTOL_ACTIVATE_FAILED"
    else:
        print(f"[ACTION_ACTIVATE][INFO] PID не предоставлен, попытка через xdotool пропускается.")

    # Если ни один из методов не сработал
    return False, "ACTIVATION_FAILED_ALL_METHODS"
