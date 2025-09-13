import sys
import os
import logging
import sqlite3
from typing import *
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters,
    ConversationHandler, CallbackContext
)
from config import BOT_TOKEN, ADMIN_ID, DB_PATH
from database import Database
from utils.helpers import setup_logging, calculate_order_total, format_order_text
# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

# Состояния бота
MAIN_MENU, CATEGORY_SELECTION, PRODUCT_SELECTION, QUANTITY_SELECTION = range(4)
AWAIT_LOCATION, AWAIT_COMMENT = range(6, 8)
ADMIN_PANEL, VIEW_ORDERS, ORDER_DETAIL = range(8, 11)
AWAIT_CLIENT_MESSAGE = 11

# Инициализация базы данных
db = Database(DB_PATH)

# ==================== ОСНОВНЫЕ ФУНКЦИИ ====================

def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info(f"User {user.first_name} (ID: {user.id}) started the bot")
    
    # Очищаем корзину при старте
    db.clear_cart(user.id)
    context.user_data.clear()
    
    keyboard = [['Одноразки', 'Жидкости', 'Вейпы']]
    
    # Добавляем кнопку админ-панели только для администратора
    if user.id == ADMIN_ID:
        keyboard.append(['👑 Админ-панель'])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    update.message.reply_text(
        "------------------------------------\n"
        "🚬 *Soft Vape* - магазин вейпов и аксессуаров\n"
        "------------------------------------\n\n"
        "Выберите категорию:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return MAIN_MENU

def handle_main_menu(update: Update, context: CallbackContext):
    text = update.message.text
    user = update.message.from_user
    
    if text in ['Одноразки', 'Жидкости', 'Вейпы']:
        context.user_data['category'] = text
        return show_category_products(update, context)
    elif text == '👑 Админ-панель' and user.id == ADMIN_ID:
        return admin_panel(update, context)
    
    update.message.reply_text("Пожалуйста, выберите категорию из меню:")
    return MAIN_MENU

def show_category_products(update: Update, context: CallbackContext):
    category = context.user_data['category']
    products = db.get_products_by_category(category)
    
    if not products:
        keyboard = [['⬅️ Назад в мен️']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        update.message.reply_text(
            f"😔 В категории '{category}' пока нет товаров в наличии.",
            reply_markup=reply_markup
        )
        return CATEGORY_SELECTION
    
    # Создаем кнопки товаров
    product_buttons = [[product['name']] for product in products]
    product_buttons.append(['⬅️ Назад в меню'])
    
    reply_markup = ReplyKeyboardMarkup(product_buttons, resize_keyboard=True)
    
    # Формируем список товаров
    product_list = "-------------------------------------\n"
    for product in products:
        product_list += f"• {product['name']} - {product['cost']} руб. ({product['quantity']} шт.)\n"
    product_list += "-------------------------------------"
    
    update.message.reply_text(
        f"🏷️ *{category}*:\n\n{product_list}\n\nВыберите товар:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return PRODUCT_SELECTION

#FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF

# ==================== ОСНОВНЫЕ ФУНКЦИИ НАВИГАЦИИ ====================

def handle_back_to_menu(update: Update, context: CallbackContext):
    """Обработчик кнопки 'Назад в меню'"""
    user = update.message.from_user
    logger.info(f"User {user.id} returning to main menu")
    
    # Очищаем временные данные
    context.user_data.pop('category', None)
    context.user_data.pop('selected_product', None)
    context.user_data.pop('quantity', None)
    
    return start(update, context)

def handle_back_to_products(update: Update, context: CallbackContext):
    """Обработчик кнопки 'Назад к товарам'"""
    user = update.message.from_user
    logger.info(f"User {user.id} returning to products")
    
    # Сохраняем категорию и возвращаемся к товарам
    if 'category' in context.user_data:
        return show_category_products(update, context)
    else:
        return start(update, context)

def handle_main_menu(update: Update, context: CallbackContext):
    text = update.message.text
    user = update.message.from_user
    
    # Обработка навигации
    if text == '⬅️ Назад в меню':
        return handle_back_to_menu(update, context)
    
    if text in ['Одноразки', 'Жидкости', 'Вейпы']:
        context.user_data['category'] = text
        return show_category_products(update, context)
    elif text == '👑 Админ-панель' and user.id == ADMIN_ID:
        return admin_panel(update, context)
    
    update.message.reply_text("Пожалуйста, выберите категорию из меню:")
    return MAIN_MENU

def show_category_products(update: Update, context: CallbackContext):
    category = context.user_data.get('category')
    if not category:
        return start(update, context)
    
    products = db.get_products_by_category(category)
    
    if not products:
        keyboard = [['⬅️ Назад в меню']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        update.message.reply_text(
            f"😔 В категории '{category}' пока нет товаров в наличии.",
            reply_markup=reply_markup
        )
        return CATEGORY_SELECTION
    
    # Создаем кнопки товаров
    product_buttons = [[product['name']] for product in products]
    product_buttons.append(['⬅️ Назад в меню'])
    
    reply_markup = ReplyKeyboardMarkup(product_buttons, resize_keyboard=True)
    
    # Формируем список товаров
    product_list = "-------------------------------------\n"
    for product in products:
        product_list += f"• {product['name']} - {product['cost']} руб. ({product['quantity']} шт.)\n"
    product_list += "-------------------------------------"
    
    update.message.reply_text(
        f"🏷️ *{category}*:\n\n{product_list}\n\nВыберите товар:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return PRODUCT_SELECTION

def handle_product_selection(update: Update, context: CallbackContext):
    text = update.message.text
    
    # Обработка навигации
    if text == '⬅️ Назад в меню':
        return handle_back_to_menu(update, context)
    
    product = db.get_product(text)
    if not product:
        update.message.reply_text("❌ Товар не найден. Выберите из списка:")
        return PRODUCT_SELECTION
    
    context.user_data['selected_product'] = product
    context.user_data['quantity'] = 1
    
    # Показываем информацию о товаре
    keyboard = [
        ['➖ Уменьшить', '➕ Увеличить'],
        ['✅ Подтвердить', '❌ Отменить заказ'],
        ['🛒 Добавить к заказу'],
        ['⬅️ Назад к товарам', '⬅️ Назад в меню']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    total_price = product['cost'] * context.user_data['quantity']
    
    update.message.reply_text(
        f"------------------------------------------\n"
        f"🎯 *Вы выбрали:* {product['name']}\n"
        f"📦 *Количество:* {context.user_data['quantity']} шт.\n"
        f"💰 *Итоговая цена:* {total_price} руб.\n"
        f"------------------------------------------\n\n"
        f"Выберите действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return QUANTITY_SELECTION

def handle_quantity_change(update: Update, context: CallbackContext):
    text = update.message.text
    product = context.user_data.get('selected_product')
    
    if not product:
        return start(update, context)
    
    # Обработка навигации
    if text == '⬅️ Назад к товарам':
        return handle_back_to_products(update, context)
    elif text == '⬅️ Назад в меню':
        return handle_back_to_menu(update, context)
    
    if text == '➕ Увеличить':
        if context.user_data['quantity'] < product['quantity']:
            context.user_data['quantity'] += 1
    elif text == '➖ Уменьшить':
        if context.user_data['quantity'] > 1:
            context.user_data['quantity'] -= 1
    
    total_price = product['cost'] * context.user_data['quantity']
    
    keyboard = [
        ['➖ Уменьшить', '➕ Увеличить'],
        ['✅ Подтвердить', '❌ Отменить заказ'],
        ['🛒 Добавить к заказу'],
        ['⬅️ Назад к товарам', '⬅️ Назад в меню']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    update.message.reply_text(
        f"------------------------------------------\n"
        f"🎯 *Вы выбрали:* {product['name']}\n"
        f"📦 *Количество:* {context.user_data['quantity']} шт.\n"
        f"💰 *Итоговая цена:* {total_price} руб.\n"
        f"------------------------------------------\n\n"
        f"Выберите действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return QUANTITY_SELECTION

def handle_cart_action(update: Update, context: CallbackContext):
    text = update.message.text
    user = update.message.from_user
    product = context.user_data.get('selected_product')
    
    if not product:
        return start(update, context)
    
    quantity = context.user_data.get('quantity', 1)
    
    # Обработка навигации
    if text == '⬅️ Назад к товарам':
        return handle_back_to_products(update, context)
    elif text == '⬅️ Назад в меню':
        return handle_back_to_menu(update, context)
    
    if text == '✅ Подтвердить':
        # Сохраняем в корзину и переходим к оформлению
        cart = db.get_cart(user.id)
        cart[product['name']] = quantity
        db.save_cart(user.id, cart)
        
        keyboard = [
            [KeyboardButton("📍 Отправить локацию", request_location=True)],
            ['❌ Отменить заказ', '⬅️ Назад к товарам']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        update.message.reply_text(
            "📍 *Отправьте вашу геолокацию для доставки:*\n\n"
            "Нажмите кнопку ниже 👇",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return AWAIT_LOCATION
        
    elif text == '❌ Отменить заказ':
        # Пункт 3.2 - Отмена покупок
        db.clear_cart(user.id)
        update.message.reply_text("❌ Заказ отменен. Корзина очищена.")
        return start(update, context)
        
    elif text == '🛒 Добавить к заказу':
        # Пункт 3.3 - Продолжение покупок
        cart = db.get_cart(user.id)
        cart[product['name']] = quantity
        db.save_cart(user.id, cart)
        
        update.message.reply_text(
            "✅ Товар добавлен в корзину! Продолжайте покупки.",
            reply_markup=ReplyKeyboardMarkup([['Одноразки', 'Жидкости', 'Вейпы']], resize_keyboard=True)
        )
        return MAIN_MENU

def handle_location(update: Update, context: CallbackContext):
    if update.message.location:
        location = f"{update.message.location.latitude}, {update.message.location.longitude}"
        context.user_data['location'] = location
        
        update.message.reply_text(
            "📝 *Напишите комментарий к заказу:*\n\n"
            "• Место встречи\n• Удобное время\n• Способ оплаты\n• Другие пожелания",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode='Markdown'
        )
        return AWAIT_COMMENT
    else:
        keyboard = [
            [KeyboardButton("📍 Отправить локацию", request_location=True)],
            ['❌ Отменить заказ', '⬅️ Назад к товарам']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        update.message.reply_text(
            "❌ Пожалуйста, отправьте вашу геолокацию с помощью кнопки ниже:",
            reply_markup=reply_markup
        )
        return AWAIT_LOCATION

def handle_comment(update: Update, context: CallbackContext):
    user = update.message.from_user
    comment = update.message.text
    location = context.user_data.get('location', 'Не указана')
    
    logger.info(f"Processing order for user {user.id}")
    
    # Получаем корзину
    cart = db.get_cart(user.id)
    logger.info(f"Cart: {cart}")
    
    if not cart:
        logger.error("Empty cart - cannot process order")
        update.message.reply_text(
            "❌ Корзина пуста. Пожалуйста, начните заново.",
            reply_markup=ReplyKeyboardMarkup([['/start']], resize_keyboard=True)
        )
        return ConversationHandler.END
    
    # Получаем ВСЕ продукты из базы для расчета
    all_products = db.get_all_products()
    logger.info(f"All products count: {len(all_products)}")
    
    # Рассчитываем итоговую сумму
    total_price = calculate_order_total(cart, all_products)
    logger.info(f"Total price: {total_price}")
    
    # Сохраняем заказ
    try:
        order_id = db.save_order(
            user.id, 
            user.first_name, 
            cart, 
            total_price, 
            location, 
            comment
        )
        
        if order_id:
            logger.info(f"Order saved with ID: {order_id}")
            
            # Формируем текст заказа
            order_text = format_order_text(cart, all_products, location, comment)
            
            # Отправляем подтверждение пользователю
            keyboard = [['/start']]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            update.message.reply_text(
                order_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            # Отправляем уведомление админу
            try:
                admin_text = f"📦 *Новый заказ #{order_id}*\n\n"
                admin_text += f"👤 Пользователь: {user.first_name} (@{user.username or 'нет'})\n"
                admin_text += f"📞 ID: {user.id}\n\n"
                admin_text += order_text
                
                context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=admin_text,
                    parse_mode='Markdown'
                )
                logger.info("Admin notification sent")
            except Exception as e:
                logger.error(f"Error sending admin notification: {e}")
            
            # Очищаем корзину
            db.clear_cart(user.id)
            context.user_data.clear()
            logger.info("Cart cleared")
            
        else:
            logger.error("Order ID is None - save_order failed")
            update.message.reply_text(
                "❌ Произошла ошибка при сохранении заказа. Попробуйте еще раз.",
                reply_markup=ReplyKeyboardMarkup([['/start']], resize_keyboard=True)
            )
            
    except Exception as e:
        logger.error(f"Error in handle_comment: {e}")
        update.message.reply_text(
            "❌ Произошла ошибка. Пожалуйста, попробуйте еще раз.",
            reply_markup=ReplyKeyboardMarkup([['/start']], resize_keyboard=True)
        )
    
    return ConversationHandler.END

# ==================== АДМИН-ПАНЕЛЬ ====================

def admin_panel(update: Update, context: CallbackContext):
    """Админ-панель"""
    user = update.message.from_user
    
    if user.id != ADMIN_ID:
        update.message.reply_text("❌ Доступ только для администратора.")
        return ConversationHandler.END
    
    # Очищаем временные данные
    context.user_data.pop('current_orders', None)
    context.user_data.pop('selected_order', None)
    context.user_data.pop('order_status', None)
    
    keyboard = [
        ['📦 Активные заказы', '✅ Завершенные'],
        ['❌ Отмененные', '🔄 Обновить товары'],
        ['🗑️ Управление товарами'],
        ['⬅️ Главное меню']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    update.message.reply_text(
        "👑 *Админ-панель Soft Vape*\n\n"
        "Выберите действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return ADMIN_PANEL

def admin_command(update: Update, context: CallbackContext):
    """Команда /admin для открытия админ-панели"""
    return admin_panel(update, context)

def handle_admin_actions(update: Update, context: CallbackContext):
    """Обработка действий в админ-панели"""
    user = update.message.from_user
    text = update.message.text
    
    if user.id != ADMIN_ID:
        update.message.reply_text("❌ Доступ только для администратора.")
        return ADMIN_PANEL
    
    # Обрабатываем кнопку "Главное меню"
    if text == '⬅️ Главное меню':
        context.user_data.clear()
        return start(update, context)
    
    # Обрабатываем кнопку "Назад в админ-панель"
    if text == '⬅️ Назад в админ-панель':
        return admin_panel(update, context)
    
    # Безопасное логирование с эмодзи
        safe_text = text.encode('ascii', 'ignore').decode('ascii') if text else 'empty'
        logger.info(f"Admin action: '{safe_text}' from user {user.id}")
    
    # УДАЛЕНО: блок статистики
    elif text == '📦 Активные заказы':
        show_orders(update, context, 'pending')
        return
        
    elif text == '✅ Завершенные':
        show_orders(update, context, 'completed')
        return
        
    elif text == '❌ Отмененные':
        show_orders(update, context, 'cancelled')
        return
        
    elif text == '🔄 Обновить товары':
        update.message.reply_text(
            "📦 Отправьте CSV файл с товарами.\n\n"
            "Формат: category,name,cost,quantity,description\n"
            "Пример: Одноразки,Elf Bar,1500,25,Вкус манго\n\n"
            "Или нажмите /cancel для отмены"
        )
        context.user_data['awaiting_csv'] = True
        return
        
    elif text == '🗑️ Управление товарами':
        keyboard = [
            ['🗑️ Очистить все товары', '📦 Заменить товары'],
            ['📋 Показать товары', '⬅️ Назад в админ-панель']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        update.message.reply_text(
            "🛍️ *Управление товарами*\n\n"
            "Выберите действие:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    # Обработка кнопок управления товарами
    elif text == '🗑️ Очистить все товары':
        keyboard = [['✅ Да, очистить', '❌ Нет, отмена']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        update.message.reply_text(
            "⚠️ *ВНИМАНИЕ!*\n\n"
            "Вы уверены, что хотите очистить ВСЕ товары из базы данных?\n"
            "Это действие нельзя отменить!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        context.user_data['awaiting_clear'] = True
        return
        
    elif text == '📦 Заменить товары':
        update.message.reply_text(
            "📦 *Замена товаров*\n\n"
            "Отправьте CSV файл с новыми товарами.\n\n"
            "Формат: category,name,cost,quantity,description\n"
            "Пример: Одноразки,Elf Bar,1500,25,Вкус манго\n\n"
            "⚠️ *ВНИМАНИЕ!* Все старые товары будут удалены!",
            parse_mode='Markdown'
        )
        context.user_data['awaiting_replace'] = True
        return
        
    elif text == '📋 Показать товары':
        show_products_list(update, context)
        return
        
    elif text == '⬅️ Назад в админ-панель':
        admin_panel(update, context)
        return
    
    # Обработка подтверждения очистки товаров
    elif text in ['✅ Да, очистить', '❌ Нет, отмена']:
        handle_clear_confirmation(update, context)
        return
    
    # Обработка кнопок управления заказами
    elif text in ['✅ Выполнить заказ', '❌ Отменить заказ', '❌ Вернуть в ожидание', '✅ Восстановить заказ', '⬅️ Назад к списку']:
        handle_order_details(update, context)
        return
    
    # Обработка выбора номера заказа
    elif text.isdigit():
        handle_order_selection(update, context)
        return
    
    # Если это не известная команда, показываем админ-панель снова
    admin_panel(update, context)

def show_products_list(update: Update, context: CallbackContext):
    """Показать список всех товаров"""
    try:
        products = db.get_all_products()
        
        if not products:
            update.message.reply_text("📭 Товары не найдены в базе данных")
            return
        
        # Группируем товары по категориям
        categories = {}
        for product in products:
            category = product['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(product)
        
        # Формируем текст
        products_text = "🛍️ *Список товаров:*\n\n"
        
        for category, category_products in categories.items():
            products_text += f"📂 *{category}:*\n"
            for product in category_products:
                products_text += f"• {product['name']} - {product['cost']} руб. (остаток: {product['quantity']} шт.)\n"
            products_text += "\n"
        
        products_text += f"📊 *Всего товаров:* {len(products)}\n"
        products_text += f"📂 *Категорий:* {len(categories)}"
        
        keyboard = [['⬅️ Назад в админ-панель']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        update.message.reply_text(
            products_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error showing products: {e}")
        update.message.reply_text(f"❌ Ошибка при получении списка товаров: {e}")

def show_orders(update: Update, context: CallbackContext, status: str):
    """Показать заказы по статусу"""
    logger.info(f"Showing orders with status: {status}")
    orders = db.get_all_orders(status)
    logger.info(f"Found {len(orders)} orders")
    
    if not orders:
        keyboard = [['⬅️ Назад в админ-панель']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        update.message.reply_text(
            f"📭 Нет заказов со статусом '{status}'",
            reply_markup=reply_markup
        )
        return
    
    context.user_data['current_orders'] = orders
    context.user_data['order_status'] = status
    
    # Создаем кнопки с заказами
    keyboard = []
    orders_text = f"📦 *Заказы ({status}):*\n\n"
    
    for i, order in enumerate(orders, 1):
        order_count = len(order['order_data'])
        orders_text += f"{i}. #{order['id']} - {order['user_name']}, {order_count}шт, {order['total_price']}руб\n"
        
        if i % 2 == 1:
            keyboard.append([str(i)])
        else:
            keyboard[-1].append(str(i))
    
    keyboard.append(['⬅️ Назад в админ-панель'])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    update.message.reply_text(
        orders_text + "\nВыберите номер заказа:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def handle_order_selection(update: Update, context: CallbackContext):
    """Обработка выбора заказа"""
    text = update.message.text
    user = update.message.from_user
    
    if user.id != ADMIN_ID:
        return
    
    if text == '⬅️ Назад в админ-панель':
        admin_panel(update, context)
        return
    
    orders = context.user_data.get('current_orders', [])
    
    if not text.isdigit():
        update.message.reply_text("❌ Пожалуйста, выберите номер заказа:")
        return
    
    order_index = int(text) - 1
    
    if order_index < 0 or order_index >= len(orders):
        update.message.reply_text("❌ Неверный номер заказа. Выберите из списка:")
        return
    
    selected_order = orders[order_index]
    context.user_data['selected_order'] = selected_order
    
    # Формируем текст заказа
    order_text = format_order_details(selected_order)
    
    # Кнопки действий в зависимости от статуса
    status = context.user_data.get('order_status', 'pending')
    keyboard = []
    
    if status == 'pending':
        keyboard = [
            ['✅ Выполнить заказ', '❌ Отменить заказ'],
            ['⬅️ Назад к списку']
        ]
    elif status == 'completed':
        keyboard = [
            ['❌ Вернуть в ожидание', '⬅️ Назад к списку']
        ]
    elif status == 'cancelled':
        keyboard = [
            ['✅ Восстановить заказ', '⬅️ Назад к списку']
        ]
    else:
        keyboard = [
            ['⬅️ Назад к списку']
        ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    update.message.reply_text(
        order_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def handle_order_details(update: Update, context: CallbackContext):
    """Обработка действий с заказом"""
    text = update.message.text
    user = update.message.from_user
    order = context.user_data.get('selected_order')
    
    if user.id != ADMIN_ID:
        return
    
    if not order:
        update.message.reply_text("❌ Заказ не найден. Возвращаемся в админ-панель.")
        admin_panel(update, context)
        return
    
    if text == '⬅️ Назад к списку':
        status = context.user_data.get('order_status', 'pending')
        show_orders(update, context, status)
        return
    
    elif text == '✅ Выполнить заказ':
        if db.update_order_status(order['id'], 'completed'):
            update.message.reply_text("✅ Заказ отмечен как выполненный")
            logger.info(f"Order {order['id']} marked as completed by admin {user.id}")
        else:
            update.message.reply_text("❌ Ошибка при обновлении статуса заказа")
        
        admin_panel(update, context)
        return
    
    elif text == '❌ Отменить заказ':
        if db.update_order_status(order['id'], 'cancelled'):
            update.message.reply_text("❌ Заказ отменен")
            logger.info(f"Order {order['id']} cancelled by admin {user.id}")
        else:
            update.message.reply_text("❌ Ошибка при отмене заказа")
        
        admin_panel(update, context)
        return
    
    elif text == '❌ Вернуть в ожидание':
        if db.update_order_status(order['id'], 'pending'):
            update.message.reply_text("🔄 Заказ возвращен в ожидание")
            logger.info(f"Order {order['id']} returned to pending by admin {user.id}")
        else:
            update.message.reply_text("❌ Ошибка при обновлении статуса заказа")
        
        admin_panel(update, context)
        return
    
    elif text == '✅ Восстановить заказ':
        if db.update_order_status(order['id'], 'pending'):
            update.message.reply_text("✅ Заказ восстановлен")
            logger.info(f"Order {order['id']} restored by admin {user.id}")
        else:
            update.message.reply_text("❌ Ошибка при восстановлении заказа")
        
        admin_panel(update, context)
        return

def handle_csv_file(update: Update, context: CallbackContext):
    """Обработка CSV файла"""
    user = update.message.from_user
    
    if user.id != ADMIN_ID:
        return
    
    if update.message.document:
        try:
            file = update.message.document.get_file()
            file_bytes = file.download_as_bytearray()
            csv_data = file_bytes.decode('utf-8')
            
            # Проверяем, что это за операция
            if context.user_data.get('awaiting_csv'):
                # Обычное обновление товаров
                success = db.import_products_from_csv(csv_data)
                
                if success:
                    update.message.reply_text("✅ База данных успешно обновлена из CSV файла!")
                else:
                    update.message.reply_text("❌ Ошибка при обработке CSV файла")
                    
            elif context.user_data.get('awaiting_replace'):
                # Замена товаров
                success = replace_products_from_csv(update, context, csv_data)
                
                if success:
                    update.message.reply_text("✅ Товары успешно заменены из CSV файла!")
                else:
                    update.message.reply_text("❌ Ошибка при замене товаров")
            else:
                update.message.reply_text("❌ Неожиданный CSV файл. Используйте команды из админ-панели.")
                
        except Exception as e:
            logger.error(f"Error processing CSV: {e}")
            update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    # Очищаем флаги
    context.user_data.pop('awaiting_csv', None)
    context.user_data.pop('awaiting_replace', None)
    admin_panel(update, context)

def replace_products_from_csv(update: Update, context: CallbackContext, csv_data: str):
    """Замена товаров из CSV файла"""
    try:
        import csv
        from io import StringIO
        
        # Создаем резервную копию текущих товаров
        backup_products = db.get_all_products()
        
        # Читаем новый CSV
        reader = csv.DictReader(StringIO(csv_data))
        new_products = []
        
        for row in reader:
            new_products.append((
                row.get('category', ''),
                row.get('name', ''),
                float(row.get('cost', 0)),
                int(row.get('quantity', 0)),
                row.get('image_path', ''),
                row.get('description', '')
            ))
        
        if not new_products:
            update.message.reply_text("❌ CSV файл пуст или некорректен")
            return False
        
        # Очищаем старые товары и добавляем новые
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Очищаем таблицу товаров
        cursor.execute("DELETE FROM products")
        
        # Добавляем новые товары
        cursor.executemany(
            "INSERT INTO products (category, name, cost, quantity, image_path, description) VALUES (?, ?, ?, ?, ?, ?)",
            new_products
        )
        
        conn.commit()
        conn.close()
        
        logger.info(f"Products replaced: {len(backup_products)} old -> {len(new_products)} new")
        return True
        
    except Exception as e:
        logger.error(f"Error replacing products from CSV: {e}")
        return False

def handle_clear_confirmation(update: Update, context: CallbackContext):
    """Обработка подтверждения очистки"""
    text = update.message.text
    user = update.message.from_user
    
    logger.info(f"Clear confirmation: '{text}' from user {user.id}")
    print(f"DEBUG: Clear confirmation: '{text}' from user {user.id}")
    
    if user.id != ADMIN_ID:
        return
    
    if not context.user_data.get('awaiting_clear'):
        logger.warning("Clear confirmation called without awaiting_clear flag")
        return
    
    if text == '✅ Да, очистить':
        try:
            logger.info("Starting products clearing process")
            
            # Создаем резервную копию перед очисткой
            backup_products = db.get_all_products()
            logger.info(f"Backup products count: {len(backup_products)}")
            
            create_products_backup(backup_products)
            
            # Очищаем товары
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Проверяем количество товаров до очистки
            cursor.execute("SELECT COUNT(*) FROM products")
            count_before = cursor.fetchone()[0]
            logger.info(f"Products count before clearing: {count_before}")
            
            cursor.execute("DELETE FROM products")
            
            # Проверяем количество товаров после очистки
            cursor.execute("SELECT COUNT(*) FROM products")
            count_after = cursor.fetchone()[0]
            logger.info(f"Products count after clearing: {count_after}")
            
            conn.commit()
            conn.close()
            
            update.message.reply_text(
                f"✅ Все товары удалены из базы данных\n"
                f"📦 Удалено товаров: {count_before}\n"
                f"💾 Резервная копия сохранена"
            )
            logger.info(f"Products cleared successfully: {count_before} items removed")
            
        except Exception as e:
            logger.error(f"Error clearing products: {e}")
            update.message.reply_text(f"❌ Ошибка при очистке товаров: {e}")
        
    elif text == '❌ Нет, отмена':
        update.message.reply_text("❌ Очистка отменена")
        logger.info("Products clearing cancelled by admin")
    
    context.user_data.pop('awaiting_clear', None)
    admin_panel(update, context)

def create_products_backup(products):
    """Создание резервной копии товаров"""
    try:
        import csv
        from datetime import datetime
        
        # Создаем имя файла с датой и временем
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_products_{timestamp}.csv"
        backup_path = os.path.join(CSV_DIR, backup_filename)
        
        # Создаем директорию если не существует
        os.makedirs(CSV_DIR, exist_ok=True)
        
        # Записываем резервную копию
        with open(backup_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['category', 'name', 'cost', 'quantity', 'image_path', 'description'])
            
            for product in products:
                writer.writerow([
                    product['category'],
                    product['name'],
                    product['cost'],
                    product['quantity'],
                    product.get('image_path', ''),
                    product.get('description', '')
                ])
        
        logger.info(f"Products backup created: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return None

def handle_db_delete_confirmation(update: Update, context: CallbackContext):
    """Обработка подтверждения удаления базы данных"""
    text = update.message.text
    
    if not context.user_data.get('awaiting_db_delete'):
        return ADMIN_PANEL
    
    if text == '✅ Да, удалить БД':
        try:
            import os
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
                update.message.reply_text("✅ База данных полностью удалена!")
                logger.info("Database file deleted")
            else:
                update.message.reply_text("❌ Файл базы данных не найден")
        except Exception as e:
            logger.error(f"Error deleting database: {e}")
            update.message.reply_text(f"❌ Ошибка при удалении базы данных: {e}")
        
    elif text == '❌ Нет, отмена':
        update.message.reply_text("❌ Удаление базы данных отменено")
    
    context.user_data.pop('awaiting_db_delete', None)
    return admin_panel(update, context)


def format_order_details(order: dict) -> str:
    """Форматирование деталей заказа"""
    order_text = f"📦 *Заказ #{order['id']}*\n\n"
    order_text += f"👤 *Клиент:* {order['user_name']}\n"
    order_text += f"📞 *ID:* {order['user_id']}\n"
    order_text += f"💰 *Сумма:* {order['total_price']} руб.\n"
    order_text += f"📋 *Статус:* {order['status']}\n"
    order_text += f"⏰ *Дата:* {order['created_at']}\n\n"
    
    order_text += "🛍️ *Состав заказа:*\n"
    for product_name, quantity in order['order_data'].items():
        order_text += f"• {product_name} x{quantity}\n"
    
    order_text += f"\n📍 *Локация:* {order['location']}\n"
    order_text += f"📝 *Комментарий:* {order['comment']}\n"
    
    return order_text
# ==================== СЛУЖЕБНЫЕ ФУНКЦИИ ====================

def handle_navigation(update: Update, context: CallbackContext):
    """Универсальный обработчик навигации"""
    text = update.message.text
    
    if text == '⬅️ Назад в меню':
        return handle_back_to_menu(update, context)
    elif text == '⬅️ Назад к товарам':
        return handle_back_to_products(update, context)
    elif text == '⬅️ Назад в админ-панель':
        return admin_panel(update, context)
    elif text == '⬅️ Главное меню':
        context.user_data.clear()
        return start(update, context)
    
    # Если команда не распознана, продолжаем текущее состояние
    return None

def stop_bot(update: Update, context: CallbackContext):
    """Команда для остановки бота (только для админа)"""
    user = update.message.from_user
    
    if user.id != ADMIN_ID:
        update.message.reply_text("❌ Эта команда доступна только администратору.")
        return
    
    update.message.reply_text("🛑 Останавливаю бота...")
    
    # Останавливаем updater
    context.dispatcher.stop()
    context.dispatcher.updater.stop()
    
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info(f"User {user.first_name} canceled the conversation.")
    
    db.clear_cart(user.id)
    context.user_data.clear()
    
    update.message.reply_text(
        "❌ Действие отменено.",
        reply_markup=ReplyKeyboardMarkup([['/start']], resize_keyboard=True)
    )
    
    return ConversationHandler.END

def error_handler(update: Update, context: CallbackContext):
    logger.error(f"Update {update} caused error {context.error}")
    
    try:
        update.message.reply_text(
            "❌ Произошла ошибка. Пожалуйста, попробуйте еще раз.",
            reply_markup=ReplyKeyboardMarkup([['/start']], resize_keyboard=True)
        )
    except:
        pass
    
    return ConversationHandler.END

def test_order(update: Update, context: CallbackContext):
    """Тестовая функция для проверки заказа"""
    user = update.message.from_user
    
    if user.id != ADMIN_ID:
        update.message.reply_text("❌ Эта команда только для администратора.")
        return
    
    # Создаем тестовую корзину
    test_cart = {'ИКСРОС 5 МИНИ': 1}
    db.save_cart(user.id, test_cart)
    
    # Переходим к оформлению
    context.user_data['location'] = "55.7558, 37.6173"  # Тестовая локация
    context.user_data['test_mode'] = True
    
    update.message.reply_text(
        "📝 *Напишите тестовый комментарий к заказу:*",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    
    return AWAIT_COMMENT

def test_db(update: Update, context: CallbackContext):
    """Тестовая функция для проверки базы данных"""
    user = update.message.from_user
    
    if user.id != ADMIN_ID:
        update.message.reply_text("❌ Эта команда только для администратора.")
        return
    
    try:
        # Проверяем товары
        products = db.get_all_products()
        products_text = f"📦 Товары в базе: {len(products)}\n"
        for product in products[:5]:  # Показываем первые 5
            products_text += f"• {product['name']} - {product['cost']} руб.\n"
        
        # Проверяем заказы
        orders = db.get_all_orders()
        orders_text = f"\n📋 Заказы в базе: {len(orders)}\n"
        for order in orders[:3]:  # Показываем первые 3
            orders_text += f"• #{order['id']} - {order['user_name']} - {order['status']}\n"
        
        update.message.reply_text(products_text + orders_text)
        
    except Exception as e:
        update.message.reply_text(f"❌ Ошибка базы данных: {e}")
        logger.error(f"Database test error: {e}")

def force_clear_products(update: Update, context: CallbackContext):
    """Принудительная очистка товаров (только для админа)"""
    user = update.message.from_user
    
    if user.id != ADMIN_ID:
        update.message.reply_text("❌ Эта команда только для администратора.")
        return
    
    try:
        # Создаем резервную копию
        backup_products = db.get_all_products()
        create_products_backup(backup_products)
        
        # Очищаем товары
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM products")
        count_before = cursor.fetchone()[0]
        
        cursor.execute("DELETE FROM products")
        
        cursor.execute("SELECT COUNT(*) FROM products")
        count_after = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        update.message.reply_text(
            f"✅ Товары принудительно очищены!\n"
            f"📦 Удалено товаров: {count_before}\n"
            f"💾 Резервная копия сохранена"
        )
        logger.info(f"Products force cleared: {count_before} items removed")
        
    except Exception as e:
        update.message.reply_text(f"❌ Ошибка при очистке: {e}")
        logger.error(f"Force clear error: {e}")

def force_reset(update: Update, context: CallbackContext):
    """Принудительный сброс состояния бота"""
    user = update.message.from_user
    logger.info(f"Force reset for user {user.id}")
    
    # Очищаем все данные
    db.clear_cart(user.id)
    context.user_data.clear()
    
    update.message.reply_text(
        "🔄 Состояние бота сброшено. Начинаем заново...",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Запускаем заново
    return start(update, context)

def kill_all_bots(update: Update, context: CallbackContext):
    """Остановить все экземпляры бота (только для админа)"""
    user = update.message.from_user
    
    if user.id != ADMIN_ID:
        update.message.reply_text("❌ Эта команда доступна только администратору.")
        return
    
    try:
        # Удаляем webhook и останавливаем polling
        context.bot.delete_webhook()
        update.message.reply_text("🛑 Все экземпляры бота остановлены!")
        logger.info("All bot instances stopped by admin command")
        
        # Останавливаем текущий экземпляр
        context.dispatcher.stop()
        context.dispatcher.updater.stop()
        
    except Exception as e:
        update.message.reply_text(f"❌ Ошибка при остановке: {e}")
        logger.error(f"Error stopping bot instances: {e}")
    
    return ConversationHandler.END

def handle_client_message(update, context):
    update.message.reply_text("Я получил твоё сообщение!")


def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Создаем основной conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                MessageHandler(Filters.text & ~Filters.command, handle_main_menu),
            ],
            CATEGORY_SELECTION: [
                MessageHandler(Filters.regex('^⬅️ Назад в меню$'), handle_back_to_menu),
                MessageHandler(Filters.text & ~Filters.command, show_category_products),
            ],
            PRODUCT_SELECTION: [
                MessageHandler(Filters.regex('^⬅️ Назад в меню$'), handle_back_to_menu),
                MessageHandler(Filters.text & ~Filters.command, handle_product_selection),
            ],
            QUANTITY_SELECTION: [
                MessageHandler(Filters.regex('^(➖ Уменьшить|➕ Увеличить)$'), handle_quantity_change),
                MessageHandler(Filters.regex('^(✅ Подтвердить|❌ Отменить заказ|🛒 Добавить к заказу)$'), handle_cart_action),
                MessageHandler(Filters.regex('^⬅️ Назад к товарам$'), handle_back_to_products),
                MessageHandler(Filters.regex('^⬅️ Назад в меню$'), handle_back_to_menu),
            ],
            AWAIT_LOCATION: [
                MessageHandler(Filters.location, handle_location),
                MessageHandler(Filters.regex('^❌ Отменить заказ$'), cancel),
                MessageHandler(Filters.regex('^⬅️ Назад к товарам$'), handle_back_to_products),
            ],
            AWAIT_COMMENT: [
                MessageHandler(Filters.text & ~Filters.command, handle_comment),
            ],
            ADMIN_PANEL: [
                MessageHandler(Filters.text & ~Filters.command, handle_admin_actions),
                MessageHandler(Filters.document.file_extension("csv"), handle_csv_file),
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel), 
            CommandHandler('start', start),
            CommandHandler('stop', stop_bot)
        ],
        allow_reentry=True
    )
    
    # Добавляем обработчики (важен порядок!)
    dp.add_handler(conv_handler)
    
    # Добавляем обработчик команды /admin
    dp.add_handler(CommandHandler('admin', admin_panel))
    
    # Обработчик ошибок
    dp.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("Бот запущен...")
    print(f"🤖 Бот запущен с токеном: {BOT_TOKEN}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print("⏳ Ожидание сообщений...")
    print("👑 Команда /admin - открыть админ-панель")
    print("📦 Админ-панель: Управление заказами и товарами")

    try:
        updater.start_polling(drop_pending_updates=True)
        updater.idle()
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        return

if __name__ == '__main__':
    main()