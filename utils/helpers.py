import logging
from typing import Dict, List

# Добавляем logger
logger = logging.getLogger(__name__)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/bot.log'),
            logging.StreamHandler()
        ]
    )

def calculate_order_total(cart: Dict, products: List[Dict]) -> float:
    total = 0.0
    logger.info(f"Calculating total for cart: {cart}")
    
    for product_name, quantity in cart.items():
        # Ищем товар по точному совпадению имени
        product = next((p for p in products if p['name'] == product_name), None)
        if product:
            product_total = quantity * product['cost']
            logger.info(f"Product: {product_name}, Qty: {quantity}, Price: {product_total}")
            total += product_total
        else:
            logger.warning(f"Product '{product_name}' not found in products list")
            # Попробуем найти по частичному совпадению
            for p in products:
                if product_name in p['name'] or p['name'] in product_name:
                    product_total = quantity * p['cost']
                    logger.info(f"Found similar: {p['name']} for {product_name}")
                    total += product_total
                    break
    
    logger.info(f"Total calculated: {total}")
    return round(total, 2)

def format_order_text(cart: Dict, products: List[Dict], location: str, comment: str) -> str:
    order_text = "✅ *Ваш заказ подтверждён!*\n\n"
    order_text += "📦 *Состав заказа:*\n"
    
    total = 0.0
    for product_name, quantity in cart.items():
        product = next((p for p in products if p['name'] == product_name), None)
        if product:
            product_total = quantity * product['cost']
            order_text += f"• {product_name} x{quantity} - {product_total} руб.\n"
            total += product_total
        else:
            # Если точное совпадение не найдено, ищем похожее
            for p in products:
                if product_name in p['name'] or p['name'] in product_name:
                    product_total = quantity * p['cost']
                    order_text += f"• {p['name']} x{quantity} - {product_total} руб.\n"
                    total += product_total
                    break
    
    order_text += f"\n💰 *Итого: {round(total, 2)} руб.*\n"
    order_text += f"📍 *Локация:* {location}\n"
    order_text += f"📝 *Комментарий:* {comment}\n\n"
    order_text += "⏳ *Мы свяжемся с вами в ближайшее время для подтверждения заказа!*"
    
    return order_text