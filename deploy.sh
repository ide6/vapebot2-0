#!/bin/bash

# Скрипт для автоматического деплоя бота на VPS
# Использование: ./deploy.sh

echo "🚀 Начинаем деплой Soft Vape Bot..."

# Проверяем, что мы в правильной директории
if [ ! -f "main.py" ]; then
    echo "❌ Ошибка: файл main.py не найден. Запустите скрипт из корневой папки проекта."
    exit 1
fi

# Проверяем наличие .env файла
if [ ! -f ".env" ]; then
    echo "⚠️  Внимание: файл .env не найден. Создайте его с переменными BOT_TOKEN и ADMIN_ID"
    echo "Пример содержимого .env:"
    echo "BOT_TOKEN=ваш_токен_бота"
    echo "ADMIN_ID=ваш_telegram_id"
    exit 1
fi

# Создаем виртуальное окружение
echo "📦 Создаем виртуальное окружение..."
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
echo "📥 Устанавливаем зависимости..."
pip install -r requirements.txt

# Создаем необходимые директории
echo "📁 Создаем директории..."
mkdir -p data
mkdir -p csv_files
mkdir -p logs
mkdir -p images/products

# Устанавливаем права доступа
echo "🔐 Настраиваем права доступа..."
chmod 755 data
chmod 755 csv_files
chmod 755 logs
chmod 755 images

# Создаем systemd сервис
echo "⚙️  Создаем systemd сервис..."
sudo tee /etc/systemd/system/vapebot.service > /dev/null <<EOF
[Unit]
Description=Soft Vape Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Перезагружаем systemd
echo "🔄 Перезагружаем systemd..."
sudo systemctl daemon-reload

# Включаем автозапуск
echo "✅ Включаем автозапуск..."
sudo systemctl enable vapebot

# Запускаем бота
echo "🚀 Запускаем бота..."
sudo systemctl start vapebot

# Проверяем статус
echo "📊 Проверяем статус..."
sleep 3
sudo systemctl status vapebot --no-pager

echo ""
echo "🎉 Деплой завершен!"
echo ""
echo "📋 Полезные команды:"
echo "  sudo systemctl status vapebot    - статус бота"
echo "  sudo systemctl restart vapebot   - перезапуск бота"
echo "  sudo systemctl stop vapebot      - остановка бота"
echo "  sudo journalctl -u vapebot -f    - просмотр логов"
echo ""
echo "🔧 Для настройки бота отредактируйте файл .env"
echo "📱 Затем перезапустите бота: sudo systemctl restart vapebot"
