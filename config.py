import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

# Пути к файлам
DB_PATH = 'data/vape_shop_new.db'  # Изменил название БД для нового бота
IMAGES_DIR = 'images/products/'
CSV_DIR = 'csv_files/'
LOGS_DIR = 'logs/'

# Создаем необходимые директории
os.makedirs('data', exist_ok=True)
os.makedirs('images/products', exist_ok=True)
os.makedirs('csv_files', exist_ok=True)
os.makedirs('logs', exist_ok=True)

print(f"Bot token: {BOT_TOKEN}")
print(f"Admin ID: {ADMIN_ID}")
print(f"Database: {DB_PATH}")