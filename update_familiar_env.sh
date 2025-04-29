#!/bin/bash

# Скрипт для обновления переменных окружения для сервиса Фамильяра
# Запускается при входе пользователя в графическую сессию

ENV_FILE="/etc/familiar/familiar_service.env"
TOKEN_LINE=$(grep '^TELEGRAM_BOT_TOKEN=' "$ENV_FILE") # Сохраняем строку с токеном

# Получаем переменные из текущей сессии
CURRENT_DISPLAY=$(echo $DISPLAY)
CURRENT_XAUTHORITY=$(echo $XAUTHORITY)
CURRENT_DBUS_SESSION_BUS_ADDRESS=$(echo $DBUS_SESSION_BUS_ADDRESS)
CURRENT_XDG_RUNTIME_DIR=$(echo $XDG_RUNTIME_DIR)

# Перезаписываем файл, сохраняя токен и добавляя переменные сессии
# Используем sudo tee, так как файл принадлежит root
{
  echo "$TOKEN_LINE" # Возвращаем токен
  echo "DISPLAY=$CURRENT_DISPLAY"
  echo "XAUTHORITY=$CURRENT_XAUTHORITY"
  echo "DBUS_SESSION_BUS_ADDRESS=$CURRENT_DBUS_SESSION_BUS_ADDRESS"
  echo "XDG_RUNTIME_DIR=$CURRENT_XDG_RUNTIME_DIR"
} | sudo tee "$ENV_FILE" > /dev/null

# Устанавливаем правильные права снова (на всякий случай)
sudo chown root:$(whoami) "$ENV_FILE" # Используем whoami для группы
sudo chmod 640 "$ENV_FILE"

echo "Familiar service environment updated at $(date)" >> ~/familiar_env_update.log # Лог для отладки