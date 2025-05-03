# File: actions/manage_system_action.py
# -*- coding: utf-8 -*-

import subprocess
import shutil
import os # Добавим os для установки переменных окружения для apt

# --- ВАЖНО: ПРЕДУПРЕЖДЕНИЕ О НЕОБХОДИМОСТИ НАСТРОЙКИ SUDOERS ---
# Хотя пользователь имеет беспарольный sudo на все, оставляем это как напоминание,
# что для работы нужен настроенный sudo без пароля для пользователя сервиса.
# --- КОНЕЦ ПРЕДУПРЕЖДЕНИЯ ---

def _run_command(command_list, capture=True):
    """
    Вспомогательная функция для запуска команды и обработки результата.
    capture: bool - Захватывать ли stdout/stderr (по умолчанию True).
    """
    command_str = " ".join(command_list)
    print(f"[ACTION_SYS][INFO] Executing: {command_str} (Capture Output: {capture})")
    try:
        # Проверка наличия команды
        cmd_to_check = command_list[1] if command_list[0] == 'sudo' else command_list[0]
        if not shutil.which(cmd_to_check):
            error_msg = f"Команда '{cmd_to_check}' не найдена."
            print(f"[ACTION_SYS][ERROR] {error_msg}")
            return False, error_msg

        # Запускаем команду
        result = subprocess.run(
            command_list,
            capture_output=capture, # Управляем захватом вывода
            text=True,
            check=False, # Не выбрасывать исключение при ошибке, обработаем сами
            encoding='utf-8'
        )

        if result.returncode == 0:
            print(f"[ACTION_SYS][SUCCESS] Command '{command_str}' executed successfully.")
            if capture:
                output = result.stdout.strip()
                return True, output if output else "Команда выполнена успешно."
            else:
                return True, "Команда выполнена успешно (вывод не захвачен)."
        else:
            stderr_output = result.stderr.strip() if capture else "(вывод не захвачен)"
            error_msg = f"Ошибка выполнения '{command_str}'. Код: {result.returncode}. Ошибка: {stderr_output}"
            print(f"[ACTION_SYS][ERROR] {error_msg}")
            return False, f"Ошибка выполнения команды. Детали в логе. Код: {result.returncode}"

    except FileNotFoundError:
        error_msg = f"Ошибка: Команда или компонент '{command_list[0]}' не найден."
        print(f"[ACTION_SYS][ERROR] {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Неизвестная ошибка при выполнении '{command_str}': {e}"
        print(f"[ACTION_SYS][ERROR] {error_msg}")
        return False, error_msg

def system_shutdown():
    """Выключает систему."""
    # Флаг -f здесь обычно не нужен, -h now достаточно
    return _run_command(['sudo', '/sbin/shutdown', '-h', 'now'], capture=False) # Не захватываем вывод

def system_reboot():
    """Перезагружает систему форсированно."""
    # Добавляем флаг -f для форсированной перезагрузки
    return _run_command(['sudo', '/sbin/reboot', '-f'], capture=False) # Не захватываем вывод

def system_update():
    """Запускает полное обновление системы (update, upgrade, dist-upgrade)."""
    # Используем apt и объединяем команды, флаг -y для автоподтверждения
    # Устанавливаем переменную окружения для неинтерактивного режима
    update_env = os.environ.copy()
    update_env["DEBIAN_FRONTEND"] = "noninteractive"

    command_str = "sudo apt update && sudo apt upgrade -y && sudo apt dist-upgrade -y"
    print(f"[ACTION_SYS][INFO] Executing complex update: {command_str}")
    try:
        # Используем shell=True с осторожностью, т.к. команда сложная с &&
        # Проверяем наличие apt перед запуском
        if not shutil.which('apt'):
             error_msg = "Команда 'apt' не найдена."
             print(f"[ACTION_SYS][ERROR] {error_msg}")
             return False, error_msg

        result = subprocess.run(
            command_str,
            shell=True, # Нужно для обработки &&
            capture_output=False, # Не захватываем вывод
            check=False, # Обработаем код возврата сами
            env=update_env # Передаем окружение для noninteractive
        )
        if result.returncode == 0:
            print(f"[ACTION_SYS][SUCCESS] System update process completed successfully.")
            return True, "Процесс обновления системы успешно завершен."
        else:
            error_msg = f"Ошибка в процессе обновления системы. Код возврата: {result.returncode}. Проверьте системные логи apt."
            print(f"[ACTION_SYS][ERROR] {error_msg}")
            return False, error_msg
    except Exception as e:
        error_msg = f"Неизвестная ошибка при запуске обновления системы: {e}"
        print(f"[ACTION_SYS][ERROR] {error_msg}")
        return False, error_msg


def get_uptime():
    """Получает время работы системы."""
    # uptime не требует sudo и вывод нам нужен
    return _run_command(['/usr/bin/uptime'], capture=True) # Захватываем вывод