# Файл: actions/close_app_action.py
# -*- coding: utf-8 -*-

import psutil # Для работы с процессами
import os     # Для os.name и os.kill (на Linux/macOS)
import signal # Для signal.SIGKILL (на Linux/macOS)

# Импортируем функцию поиска PID из соседнего модуля manage_app_action
from .manage_app_action import find_running_process_pid

def close_application_by_name(app_name_or_path):
    """
    Пытается найти и завершить процесс приложения по имени/пути.
    Возвращает True, если процесс был найден и команда на завершение отправлена/успешна,
    False если процесс не найден или произошла ошибка.
    """
    print(f"[ACTION_CLOSE][INFO] Попытка закрыть приложение: '{app_name_or_path}'")
    pid_to_close = find_running_process_pid(app_name_or_path) # Используем нашу функцию поиска PID

    if pid_to_close:
        try:
            process = psutil.Process(pid_to_close)
            process_name = process.name()
            print(f"[ACTION_CLOSE][INFO] Найден процесс '{process_name}' (PID: {pid_to_close}). Пытаемся завершить...")
            process.terminate() # Пробуем мягко
            try:
                process.wait(timeout=3)
                print(f"[ACTION_CLOSE][SUCCESS] Процесс '{process_name}' (PID: {pid_to_close}) успешно завершен (terminate).")
                return True
            except psutil.TimeoutExpired:
                print(f"[ACTION_CLOSE][WARN] Процесс '{process_name}' не завершился штатно за 3 сек. Попытка kill...")
                if os.name == 'nt': process.kill()
                else: os.kill(pid_to_close, signal.SIGKILL) # Пробуем жестко
                try:
                    process.wait(timeout=1)
                    print(f"[ACTION_CLOSE][SUCCESS] Процесс '{process_name}' (PID: {pid_to_close}) завершен после kill.")
                except psutil.TimeoutExpired:
                    print(f"[ACTION_CLOSE][ERROR] Процесс '{process_name}' (PID: {pid_to_close}) не завершился даже после kill!")
                    return False
                return True
        except psutil.NoSuchProcess:
            print(f"[ACTION_CLOSE][WARN] Процесс с PID {pid_to_close} уже не существует.")
            return True
        except psutil.AccessDenied:
            print(f"[ACTION_CLOSE][ERROR] Нет прав для завершения процесса '{process_name}' (PID: {pid_to_close}).")
            return False
        except Exception as e:
            print(f"[ACTION_CLOSE][ERROR] Неизвестная ошибка при попытке завершить процесс PID {pid_to_close}: {e}")
            return False
    else:
        print(f"[ACTION_CLOSE][INFO] Процесс для '{app_name_or_path}' не найден, закрывать нечего.")
        return True # Считаем успехом, так как процесса и так нет