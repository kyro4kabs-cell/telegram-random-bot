import random
import telebot

TOKEN = "8966738677:AAGRgPalRgc1C4xgHzNLHB7Eq9VRzjFRvxo"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if not message.text:
        return
        
    if "выбери" in message.text.lower():
        chat_id = message.chat.id
        
        # Проверяем, что это группа
        if message.chat.type not in ['group', 'supergroup']:
            bot.reply_to(message, "⚠️ Работаю только в группах!")
            return
        
        try:
            # Получаем список администраторов (включает всех участников, если бот админ)
            admins = bot.get_chat_administrators(chat_id)
            
            # Собираем всех пользователей (кроме ботов)
            users = []
            for admin in admins:
                if not admin.user.is_bot:
                    users.append(admin.user)
            
            # Если есть права на получение всех участников
            try:
                members = bot.get_chat_members(chat_id)
                for member in members:
                    if not member.user.is_bot and member.user not in users:
                        users.append(member.user)
            except:
                pass  # Если не получается получить всех, используем только администраторов
            
            if len(users) < 2:
                bot.reply_to(message, "👀 Мало людей для выбора!")
                return
            
            chosen = random.choice(users)
            
            if chosen.username:
                bot.reply_to(message, f"@{chosen.username}")
            else:
                bot.reply_to(message, chosen.first_name or "Кто-то")
                
        except Exception as e:
            print(f"Ошибка: {e}")
            bot.reply_to(message, "❌ Ошибка! Проверьте, что бот администратор")

print("🤖 Бот запущен! Реагирует на слово 'выбери'")
print("✅ Добавьте бота в группу и сделайте администратором")

bot.polling(none_stop=True)