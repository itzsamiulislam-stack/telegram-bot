import sqlite3
import telebot
from telebot import types
import requests
from datetime import datetime, timedelta
import threading

TOKEN = "YOUR_BOT_TOKEN"
API_URL = "https://your-render-url.onrender.com"

bot = telebot.TeleBot(TOKEN)

# DB
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
balance REAL DEFAULT 0,
ad_time TEXT,
ad_count INTEGER DEFAULT 0,
ad_date TEXT
)
""")
conn.commit()

AD_REWARD = 5
WAIT = 10
MAX_AD = 10

# USER
def get_user(uid):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    return cursor.fetchone()

def add_user(uid):
    if not get_user(uid):
        cursor.execute("INSERT INTO users(user_id) VALUES(?)", (uid,))
        conn.commit()

# START
@bot.message_handler(commands=['start'])
def start(msg):
    add_user(msg.from_user.id)

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📺 Watch Ad", "💰 Balance")

    bot.send_message(msg.chat.id, "Welcome!", reply_markup=kb)

# BALANCE
@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def balance(msg):
    user = get_user(msg.from_user.id)
    bot.send_message(msg.chat.id, f"💰 Balance: {user[1]} টাকা")

# WATCH AD
@bot.message_handler(func=lambda m: m.text == "📺 Watch Ad")
def ad(msg):
    uid = msg.from_user.id
    user = get_user(uid)

    today = datetime.now().strftime("%Y-%m-%d")

    if user[4] != today:
        cursor.execute("UPDATE users SET ad_count=0, ad_date=? WHERE user_id=?", (today, uid))
        conn.commit()
        user = get_user(uid)

    if user[3] >= MAX_AD:
        bot.send_message(msg.chat.id, "আজকের limit শেষ")
        return

    link = f"{API_URL}/go?user={uid}"

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔗 Open Link", url=link))
    kb.add(types.InlineKeyboardButton("✅ Claim", callback_data="claim"))

    bot.send_message(msg.chat.id,
                     "🔴 লিংকে ঢুকুন তারপর Claim চাপুন",
                     reply_markup=kb)

# CLAIM
@bot.callback_query_handler(func=lambda c: c.data == "claim")
def claim(call):
    uid = call.from_user.id

    try:
        res = requests.get(f"{API_URL}/verify?user={uid}")
        data = res.json()
    except:
        bot.answer_callback_query(call.id, "Server error", show_alert=True)
        return

    if data.get("status") != "ok":
        bot.answer_callback_query(call.id, "❌ আগে লিংকে ঢুকুন!", show_alert=True)
        return

    user = get_user(uid)

    new_balance = user[1] + AD_REWARD
    new_count = user[3] + 1
    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
    UPDATE users SET balance=?, ad_count=?, ad_date=?
    WHERE user_id=?
    """, (new_balance, new_count, today, uid))

    conn.commit()

    bot.answer_callback_query(call.id, "✅ Reward added!")

    bot.send_message(call.message.chat.id,
                     f"💰 +{AD_REWARD} টাকা\nBalance: {new_balance}")

# RUN
print("Bot running...")
bot.infinity_polling()
