import csv
from database import Database
from config import DB_PATH

def create_sample_csv():
    sample_data = [
        ['category', 'name', 'cost', 'quantity', 'image_path', 'description'],
        ['Одноразки', 'Elf Bar BC5000 Манго', 1500, 15, '', '1500 тяг, вкус манго'],
        ['Одноразки', 'HQD Cuvie Plus Кола', 1200, 20, '', '1200 тяг, вкус колы'],
        ['Одноразки', 'Maskking Axi 1500 Арбуз', 1700, 8, '', '1500 тяг, вкус арбуза'],
        ['Одноразки', 'Ivy Mango Peach', 1400, 12, '', 'Вкус манго и персика'],
        ['Жидкости', 'Pod Salt 20mg Манго', 800, 25, '', 'Солевая жидкость 20mg'],
        ['Жидкости', 'Elfliq 20mg Кола', 750, 18, '', 'Солевая жидкость 20mg'],
        ['Жидкости', 'Jam Monster Blackberry', 900, 10, '', 'Вкус ежевики'],
        ['Вейпы', 'Voopoo Drag X Plus', 4500, 5, '', 'Мощный бокс-мод 200W'],
        ['Вейпы', 'GeekVape Aegis Legend 2', 5200, 3, '', 'Защищенный бокс-мод'],
        ['Вейпы', 'Smok Nord 4', 3500, 7, '', 'Компактный под-мод'],
        ['Аксессуары', 'Сменные картриджи', 300, 30, '', 'Универсальные картриджи'],
        ['Аксессуары', 'Зарядное устройство', 500, 15, '', 'USB-C зарядка'],
        ['Аксессуары', 'Чехол для вейпа', 400, 20, '', 'Защитный чехол']
    ]
    
    with open('csv_files/products_new.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(sample_data)
    
    print("Создан файл csv_files/products_new.csv")

def import_initial_data():
    db = Database(DB_PATH)
    
    try:
        with open('csv_files/products_new.csv', 'r', encoding='utf-8') as f:
            csv_data = f.read()
        
        success = db.import_products_from_csv(csv_data)
        
        if success:
            print("✅ База данных нового бота успешно заполнена!")
            products = db.get_all_products()
            print(f"Загружено {len(products)} товаров:")
            
            categories = {}
            for product in products:
                if product['category'] not in categories:
                    categories[product['category']] = 0
                categories[product['category']] += 1
            
            for category, count in categories.items():
                print(f"  - {category}: {count} товаров")
                
        else:
            print("❌ Ошибка при импорте данных в новую БД")
            
    except FileNotFoundError:
        print("❌ Файл csv_files/products_new.csv не найден")
        create_sample_csv()
        print("✅ Файл создан, запустите снова для импорта")

if __name__ == '__main__':
    print("🔄 Инициализация нового бота SoftVape...")
    print(f"📁 База данных: {DB_PATH}")
    import_initial_data()