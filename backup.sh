#!/bin/bash

# Скрипт для резервного копирования данных бота
# Использование: ./backup.sh

echo "💾 Начинаем резервное копирование..."

# Настройки
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/$USER/backups"
BOT_DIR=$(pwd)

# Создаем директорию для бэкапов
mkdir -p $BACKUP_DIR

echo "📁 Создаем резервную копию базы данных..."
# Копируем базу данных
if [ -f "$BOT_DIR/data/vape_shop_new.db" ]; then
    cp "$BOT_DIR/data/vape_shop_new.db" "$BACKUP_DIR/vape_shop_$DATE.db"
    echo "✅ База данных скопирована: vape_shop_$DATE.db"
else
    echo "⚠️  База данных не найдена"
fi

echo "📁 Создаем резервную копию товаров..."
# Копируем резервные копии товаров
if [ -d "$BOT_DIR/csv_files" ]; then
    cp -r "$BOT_DIR/csv_files" "$BACKUP_DIR/csv_files_$DATE"
    echo "✅ Резервные копии товаров скопированы: csv_files_$DATE"
else
    echo "⚠️  Папка с резервными копиями товаров не найдена"
fi

echo "📁 Создаем резервную копию логов..."
# Копируем логи
if [ -d "$BOT_DIR/logs" ]; then
    cp -r "$BOT_DIR/logs" "$BACKUP_DIR/logs_$DATE"
    echo "✅ Логи скопированы: logs_$DATE"
else
    echo "⚠️  Папка с логами не найдена"
fi

echo "📁 Создаем резервную копию конфигурации..."
# Копируем конфигурационные файлы
cp "$BOT_DIR/.env" "$BACKUP_DIR/.env_$DATE" 2>/dev/null || echo "⚠️  Файл .env не найден"
cp "$BOT_DIR/main.py" "$BACKUP_DIR/main.py_$DATE" 2>/dev/null || echo "⚠️  Файл main.py не найден"

echo "🧹 Очищаем старые бэкапы (старше 30 дней)..."
# Удаляем старые бэкапы
find $BACKUP_DIR -name "*.db" -mtime +30 -delete 2>/dev/null
find $BACKUP_DIR -name "csv_files_*" -mtime +30 -exec rm -rf {} \; 2>/dev/null
find $BACKUP_DIR -name "logs_*" -mtime +30 -exec rm -rf {} \; 2>/dev/null
find $BACKUP_DIR -name ".env_*" -mtime +30 -delete 2>/dev/null
find $BACKUP_DIR -name "main.py_*" -mtime +30 -delete 2>/dev/null

echo "📊 Статистика резервного копирования:"
echo "  📁 Директория бэкапов: $BACKUP_DIR"
echo "  📅 Дата: $DATE"
echo "  💾 Размер бэкапа: $(du -sh $BACKUP_DIR | cut -f1)"

echo ""
echo "✅ Резервное копирование завершено!"
echo ""
echo "📋 Для восстановления используйте:"
echo "  cp $BACKUP_DIR/vape_shop_$DATE.db $BOT_DIR/data/vape_shop_new.db"
echo "  cp -r $BACKUP_DIR/csv_files_$DATE/* $BOT_DIR/csv_files/"
echo ""
echo "⏰ Для автоматического бэкапа добавьте в crontab:"
echo "  0 2 * * * $BOT_DIR/backup.sh >> $BOT_DIR/backup.log 2>&1"
