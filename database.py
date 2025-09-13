import os
import sqlite3
import json
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Таблица товаров
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                name TEXT NOT NULL UNIQUE,
                cost REAL NOT NULL,
                quantity INTEGER NOT NULL,
                image_path TEXT,
                description TEXT
            )
        ''')
        
        # Таблица корзин
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS carts (
                user_id INTEGER PRIMARY KEY,
                cart_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица заказов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_name TEXT,
                order_data TEXT,
                total_price REAL,
                location TEXT,
                comment TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    def get_all_products(self) -> List[Dict]:
        """Получить все товары"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT name, cost, quantity, image_path, category, description FROM products ORDER BY category, name"
            )
            return [{
                'name': row[0], 
                'cost': row[1], 
                'quantity': row[2], 
                'image_path': row[3],
                'category': row[4],
                'description': row[5]
            } for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting all products: {e}")
            return []
    def get_products_by_category(self, category: str) -> List[Dict]:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT name, cost, quantity, image_path FROM products WHERE category = ? AND quantity > 0 ORDER BY name",
                (category,)
            )
            return [{
                'name': row[0], 
                'cost': row[1], 
                'quantity': row[2], 
                'image_path': row[3]
            } for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting products by category: {e}")
            return []
    
    def get_product(self, name: str) -> Optional[Dict]:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT name, cost, quantity, image_path FROM products WHERE name = ?",
                (name,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    'name': row[0], 
                    'cost': row[1], 
                    'quantity': row[2], 
                    'image_path': row[3]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting product: {e}")
            return None
    
    def update_product_quantity(self, name: str, quantity: int):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE products SET quantity = quantity - ? WHERE name = ? AND quantity >= ?",
                (quantity, name, quantity)
            )
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating product quantity: {e}")
            return False
    
    def save_cart(self, user_id: int, cart_data: Dict):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO carts (user_id, cart_data, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (user_id, json.dumps(cart_data))
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error saving cart: {e}")
    
    def get_cart(self, user_id: int) -> Dict:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT cart_data FROM carts WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            return json.loads(row[0]) if row else {}
        except Exception as e:
            logger.error(f"Error getting cart: {e}")
            return {}
    
    def save_order(self, user_id: int, user_name: str, order_data: Dict, total_price: float, location: str, comment: str):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO orders (user_id, user_name, order_data, total_price, location, comment) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, user_name, json.dumps(order_data), total_price, location, comment)
            )
            self.conn.commit()
            order_id = cursor.lastrowid
            logger.info(f"Order #{order_id} saved successfully for user {user_id}")
            return order_id
        except Exception as e:
            logger.error(f"Error saving order: {e}")
            return None
    
    def clear_cart(self, user_id: int):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "DELETE FROM carts WHERE user_id = ?",
                (user_id,)
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error clearing cart: {e}")
    
    def import_products_from_csv(self, csv_data: str):
        try:
            import csv
            from io import StringIO
            
            cursor = self.conn.cursor()
            
            # Читаем CSV
            reader = csv.DictReader(StringIO(csv_data))
            products = []
            
            for row in reader:
                products.append((
                    row.get('category', ''),
                    row.get('name', ''),
                    float(row.get('cost', 0)),
                    int(row.get('quantity', 0)),
                    row.get('image_path', ''),
                    row.get('description', '')
                ))
            
            # Очищаем и заполняем таблицу
            cursor.execute("DELETE FROM products")
            cursor.executemany(
                "INSERT INTO products (category, name, cost, quantity, image_path, description) VALUES (?, ?, ?, ?, ?, ?)",
                products
            )
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error importing products from CSV: {e}")
            return False
    
    def get_all_orders(self, status: str = None) -> List[Dict]:
        """Получить все заказы с возможностью фильтрации по статусу"""
        try:
            cursor = self.conn.cursor()
            if status:
                cursor.execute("""
                    SELECT id, user_id, user_name, order_data, total_price, 
                           location, comment, status, created_at 
                    FROM orders WHERE status = ? ORDER BY created_at DESC
                """, (status,))
            else:
                cursor.execute("""
                    SELECT id, user_id, user_name, order_data, total_price, 
                           location, comment, status, created_at 
                    FROM orders ORDER BY created_at DESC
                """)
            
            orders = []
            for row in cursor.fetchall():
                orders.append({
                    'id': row[0],
                    'user_id': row[1],
                    'user_name': row[2],
                    'order_data': json.loads(row[3]),
                    'total_price': row[4],
                    'location': row[5],
                    'comment': row[6],
                    'status': row[7],
                    'created_at': row[8]
                })
            return orders
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []

    def update_order_status(self, order_id: int, status: str) -> bool:
        """Обновить статус заказа"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                (status, order_id)
            )
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            return False

    def get_order_by_id(self, order_id: int) -> Optional[Dict]:
        """Получить заказ по ID"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, user_id, user_name, order_data, total_price, 
                       location, comment, status, created_at 
                FROM orders WHERE id = ?
            """, (order_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'user_id': row[1],
                    'user_name': row[2],
                    'order_data': json.loads(row[3]),
                    'total_price': row[4],
                    'location': row[5],
                    'comment': row[6],
                    'status': row[7],
                    'created_at': row[8]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting order by ID: {e}")
            return None