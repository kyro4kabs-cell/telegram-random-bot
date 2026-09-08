import random
import telebot
import time
from datetime import datetime

TOKEN = "8966738677:AAGRgPalRgc1C4xgHzNLHB7Eq9VRzjFRvxo"
bot = telebot.TeleBot(TOKEN)

# Хранилище для статистики и истории
stats = {}
last_users = {}
user_history = {}

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if not message.text:
        return
    
    chat_id = message.chat.id
    text_lower = message.text.lower()
    
    # Команда /stats - показать статистику
    if text_lower == "/stats" or text_lower == "/статистика":
        show_stats(message, chat_id)
        return
    
    # Команда /reset - сбросить историю
    if text_lower == "/reset" or text_lower == "/сброс":
        reset_history(message, chat_id)
        return
    
    # Команда /help - помощь
    if text_lower == "/help" or text_lower == "/помощь":
        show_help(message)
        return
    
    # Основная функция - "выбери"
    if "выбери" in text_lower:
        process_pick(message, chat_id)

def show_stats(message, chat_id):
    """Показать статистику выборов"""
    if chat_id not in stats:
        bot.reply_to(message, "📊 Статистики пока нет! Напиши 'выбери' чтобы начать.")
        return
    
    total = stats[chat_id].get('total', 0)
    last_pick = stats[chat_id].get('last_pick', 'Нет данных')
    most_picked = stats[chat_id].get('most_picked', 'Нет данных')
    
    response = f"""📊 **Статистика выборов:**

🎯 Всего выборов: {total}
👤 Чаще всех выбирали: {most_picked}
⏰ Последний выбор: {last_pick}

Напиши 'выбери' для нового выбора!"""
    
    bot.reply_to(message, response, parse_mode='Markdown')

def reset_history(message, chat_id):
    """Сбросить историю"""
    if chat_id in stats:
        stats[chat_id] = {'total': 0, 'most_picked': 'Нет данных', 'last_pick': 'Нет данных'}
    if chat_id in last_users:
        last_users[chat_id] = []
    if chat_id in user_history:
        user_history[chat_id] = {}
    
    bot.reply_to(message, "🔄 История сброшена!")

def show_help(message):
    """Показать помощь"""
    help_text = """🤖 **Помощь по боту:**

🎯 **Основные команды:**
• `выбери` - выбрать случайного человека
• `выбери @username` - выбрать, исключая указанного
• `выбери 3` - выбрать 3 случайных человека

📊 **Дополнительно:**
• `/stats` или `/статистика` - показать статистику
• `/reset` или `/сброс` - сбросить историю
• `/help` или `/помощь` - это сообщение

⚙️ **Как работает:**
• Полностью случайный выбор
• Можно исключать ботов
• Ведёт статистику выборов

💡 **Примеры:**
`выбери` - случайный человек
`выбери @ivan` - случайный, кроме Ивана
`выбери 5` - выбрать 5 человек"""
    
    bot.reply_to(message, help_text, parse_mode='Markdown')

def process_pick(message, chat_id):
    """Основная функция выбора"""
    try:
        # Проверка на группу
        if message.chat.type not in ['group', 'supergroup']:
            bot.reply_to(message, "⚠️ Работаю только в группах!")
            return
        
        # Получаем всех участников
        users = get_all_users(chat_id)
        
        if len(users) < 2:
            bot.reply_to(message, "👀 Слишком мало людей для выбора!")
            return
        
        # Разбираем аргументы
        args = message.text.split()
        exclude_username = None
        count = 1
        
        # Проверяем аргументы
        for arg in args[1:]:
            if arg.startswith('@'):
                exclude_username = arg.replace('@', '').lower()
            elif arg.isdigit():
                count = min(int(arg), 10)  # Максимум 10 человек
        
        # Фильтруем пользователей
        available_users = filter_users(users, exclude_username, chat_id, message)
        
        if not available_users:
            bot.reply_to(message, f"❌ Некого выбирать! Исключён @{exclude_username}")
            return
        
        # Случайный выбор
        if count == 1:
            chosen = random.choice(available_users)
            result = format_user(chosen)
        else:
            # Выбираем несколько человек
            chosen_list = random.sample(available_users, min(count, len(available_users)))
            result = "🎯 **Выбраны:**\n" + "\n".join([f"• {format_user(u)}" for u in chosen_list])
        
        # Обновляем статистику
        update_stats(chat_id, chosen if count == 1 else chosen_list)
        
        # Отправляем результат
        if count == 1:
            bot.reply_to(message, f"🎯 **Выбор пал на:** {result}!")
        else:
            bot.reply_to(message, result, parse_mode='Markdown')
            
    except Exception as e:
        print(f"Ошибка: {e}")
        bot.reply_to(message, "❌ Ошибка! Проверьте права администратора")

def get_all_users(chat_id):
    """Получить всех пользователей чата"""
    users = []
    
    try:
        # Получаем администраторов
        admins = bot.get_chat_administrators(chat_id)
        for admin in admins:
            if not admin.user.is_bot:
                users.append(admin.user)
        
        # Пытаемся получить всех участников
        try:
            members = bot.get_chat_members(chat_id)
            for member in members:
                if not member.user.is_bot and member.user not in users:
                    users.append(member.user)
        except:
            pass
            
    except Exception as e:
        print(f"Ошибка получения пользователей: {e}")
    
    return users

def filter_users(users, exclude_username, chat_id, message):
    """Фильтровать пользователей по условиям"""
    filtered = users.copy()
    
    # Исключаем указанного пользователя
    if exclude_username:
        filtered = [u for u in filtered if not (u.username and u.username.lower() == exclude_username)]
    
    # Исключаем последних 3 выбранных (опционально)
    # Раскомментируй, если хочешь исключать последних
    # if chat_id in last_users and last_users[chat_id]:
    #     exclude_ids = [u.id for u in last_users[chat_id][-3:]]
    #     filtered = [u for u in filtered if u.id not in exclude_ids]
    
    return filtered

def format_user(user):
    """Форматировать пользователя для вывода"""
    if user.username:
        return f"@{user.username}"
    elif user.first_name:
        return user.first_name
    else:
        return "Кто-то"

def update_stats(chat_id, chosen):
    """Обновить статистику"""
    if chat_id not in stats:
        stats[chat_id] = {'total': 0, 'most_picked': 'Нет данных', 'last_pick': 'Нет данных', 'users': {}}
    
    stats[chat_id]['total'] += 1
    stats[chat_id]['last_pick'] = datetime.now().strftime("%H:%M:%S")
    
    # Обновляем статистику по пользователям
    if chat_id not in user_history:
        user_history[chat_id] = {}
    
    if isinstance(chosen, list):
        for u in chosen:
            user_id = u.id
            user_history[chat_id][user_id] = user_history[chat_id].get(user_id, 0) + 1
    else:
        user_id = chosen.id
        user_history[chat_id][user_id] = user_history[chat_id].get(user_id, 0) + 1
    
    # Находим самого частого
    if user_history[chat_id]:
        most_picked_id = max(user_history[chat_id], key=user_history[chat_id].get)
        # Ищем пользователя по ID (упрощённо)
        stats[chat_id]['most_picked'] = f"ID: {most_picked_id} ({user_history[chat_id][most_picked_id]} раз)"
    
    # Сохраняем последних выбранных
    if chat_id not in last_users:
        last_users[chat_id] = []
    
    if isinstance(chosen, list):
        last_users[chat_id].extend(chosen)
    else:
        last_users[chat_id].append(chosen)
    
    # Оставляем только последних 10
    if len(last_users[chat_id]) > 10:
        last_users[chat_id] = last_users[chat_id][-10:]

print("🤖 Бот запущен!")
print("🎲 Доступные команды:")
print("   выбери - случайный человек")
print("   выбери @username - исключая пользователя")
print("   выбери 5 - выбрать 5 человек")
print("   /stats - статистика")
print("   /help - помощь")

while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(5)
