import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import random
import os

# --- ENV VARIABLES ---
BOT_TOKEN = os.environ.get('8760694865:AAGAls1HBy8H81_oJeWPJPQksWLRc0exFe4')
ADMIN_ID = int(os.environ.get('8319697870', 0))
CHANNEL = os.environ.get('CHANNEL', '@earnmasterybd')

bot = telebot.TeleBot(BOT_TOKEN)

# --- DATABASE SETUP ---
conn = sqlite3.connect('bot_database.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, balance REAL, total_earned REAL, referrals INTEGER, lang TEXT)''')
conn.commit()

# --- HELPER FUNCTIONS ---
def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (user_id, balance, total_earned, referrals, lang) VALUES (?, 0.0, 0.0, 0, 'EN')", (user_id,))
        conn.commit()
        return (user_id, 0.0, 0.0, 0, 'EN')
    return user

def update_balance(user_id, amount):
    user = get_user(user_id)
    new_balance = user[1] + amount
    new_earned = user[2] + amount if amount > 0 else user[2]
    cursor.execute("UPDATE users SET balance=?, total_earned=? WHERE user_id=?", (new_balance, new_earned, user_id))
    conn.commit()

# --- KEYBOARDS ---
def main_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📝 Tasks", callback_data="tasks"),
        InlineKeyboardButton("👤 Profile", callback_data="profile"),
        InlineKeyboardButton("💰 Withdraw", callback_data="withdraw"),
        InlineKeyboardButton("👥 Referrals", callback_data="referrals"),
        InlineKeyboardButton("🎡 Wheel", callback_data="wheel"),
        InlineKeyboardButton("📊 Leaderboard", callback_data="leaderboard")
    )
    markup.add(InlineKeyboardButton("📢 Advertiser (Deposit)", callback_data="deposit"))
    return markup

def admin_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("👤 User Info", callback_data="admin_user"),
        InlineKeyboardButton("💰 Add Balance", callback_data="admin_add_bal"),
        InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
        InlineKeyboardButton("📊 Stats", callback_data="admin_stats")
    )
    return markup

# --- START COMMAND ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    get_user(user_id) # Register user if new
    
    # Referral Logic
    if len(message.text.split()) > 1:
        ref_id = message.text.split()[1]
        if ref_id.isdigit() and int(ref_id) != user_id:
            cursor.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id=?", (int(ref_id),))
            update_balance(int(ref_id), 1.0) # 1 BDT per refer
            bot.send_message(int(ref_id), f"🎉 You got a new referral! +1.0 BDT added.")
    
    text = f"👋 Hello {message.chat.first_name}!\n\nWelcome to **The Open Earn Bot (BD Version)** 🚀\nComplete tasks, invite friends, and earn real money!\n\nSelect an option below:"
    bot.send_message(user_id, text, reply_markup=main_menu(), parse_mode="Markdown")

# --- ADMIN COMMAND ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id == ADMIN_ID:
        bot.send_message(ADMIN_ID, "🛠️ **Advanced Admin Panel**\nControl the whole system from here:", reply_markup=admin_menu(), parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "❌ You are not an admin!")

# --- INLINE BUTTON HANDLER ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id
    user = get_user(user_id)
    
    if call.data == "back":
        bot.edit_message_text("🏠 **Main Menu:**", chat_id=user_id, message_id=call.message.message_id, reply_markup=main_menu(), parse_mode="Markdown")
        
    elif call.data == "profile":
        text = f"👤 **Your Profile**\n\n🆔 ID: `{user_id}`\n💰 Balance: {user[1]:.2f} BDT\n💵 Total Earned: {user[2]:.2f} BDT\n👥 Referrals: {user[3]}"
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="back"))
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        
    elif call.data == "referrals":
        bot_user = bot.get_me().username
        ref_link = f"https://t.me/{bot_user}?start={user_id}"
        text = f"👥 **Referral System**\n\nEarn 1.0 BDT for every valid invite!\n\n🔗 Your Link:\n`{ref_link}`\n\nTotal Invites: {user[3]}"
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="back"))
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "wheel":
        text = "🎡 **Spin The Wheel**\n\nCost: Free Spin (Once per day)\nWin up to 5 BDT!"
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🎯 Spin Now", callback_data="spin_action"), InlineKeyboardButton("🔙 Back", callback_data="back"))
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "spin_action":
        reward = round(random.uniform(0.1, 2.0), 2)
        update_balance(user_id, reward)
        text = f"🎉 **Congratulations!**\n\nYou spun the wheel and won **{reward} BDT**! 💸"
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="back"))
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "tasks":
        text = f"📝 **Available Tasks**\n\n1. Join Official Channel\nReward: 2.0 BDT"
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("Go to Channel", url=f"https://t.me/{CHANNEL.replace('@', '')}"),
            InlineKeyboardButton("✅ Verify", callback_data="verify_task")
        ).add(InlineKeyboardButton("🔙 Back", callback_data="back"))
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "verify_task":
        try:
            status = bot.get_chat_member(CHANNEL, user_id).status
            if status in ['member', 'administrator', 'creator']:
                update_balance(user_id, 2.0)
                bot.answer_callback_query(call.id, "✅ Task Completed! 2.0 BDT Added.", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "❌ You have not joined the channel yet!", show_alert=True)
        except:
            bot.answer_callback_query(call.id, "⚠️ Error verifying task. Admin needs to make bot admin in channel.", show_alert=True)

    elif call.data == "withdraw":
        text = "💳 **Withdraw System**\n\nMinimum Withdraw: 50 BDT\n\nSelect Method:"
        markup = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton("bKash", callback_data="req_bkash"),
            InlineKeyboardButton("Nagad", callback_data="req_nagad"),
            InlineKeyboardButton("USDT", callback_data="req_usdt"),
            InlineKeyboardButton("🔙 Back", callback_data="back")
        )
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data.startswith("req_"):
        method = call.data.split('_')[1].upper()
        if user[1] < 50.0:
            bot.answer_callback_query(call.id, "❌ Minimum withdrawal is 50 BDT!", show_alert=True)
            return
        msg = bot.send_message(user_id, f"📝 Enter your **{method}** account number/address:")
        bot.register_next_step_handler(msg, process_withdraw, method, user[1])

    elif call.data == "deposit":
        text = "📢 **Advertiser Deposit Panel**\n\nSend money to:\nbKash/Nagad: `017XXXXXXXX`\n\nAfter sending, submit your Transaction ID."
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🧾 Submit Txn ID", callback_data="submit_txn"), InlineKeyboardButton("🔙 Back", callback_data="back"))
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "submit_txn":
        msg = bot.send_message(user_id, "📝 Please enter your Transaction ID and Amount (e.g., TXN12345 500):")
        bot.register_next_step_handler(msg, process_deposit)

    # --- ADMIN CALLBACKS ---
    elif call.data == "admin_stats":
        cursor.execute("SELECT COUNT(*), SUM(balance) FROM users")
        data = cursor.fetchone()
        text = f"📊 **Bot Analytics**\n\nTotal Users: {data[0]}\nTotal User Balance: {data[1]:.2f} BDT"
        bot.send_message(ADMIN_ID, text, parse_mode="Markdown")

    elif call.data == "admin_broadcast":
        msg = bot.send_message(ADMIN_ID, "📝 Send the message you want to broadcast to all users:")
        bot.register_next_step_handler(msg, process_broadcast)

def process_withdraw(message, method, amount):
    number = message.text
    update_balance(message.chat.id, -amount)
    bot.send_message(message.chat.id, "✅ Your withdrawal request has been submitted to admin.")
    bot.send_message(ADMIN_ID, f"🚨 **New Withdraw Request**\n\nUser: `{message.chat.id}`\nMethod: {method}\nNumber: `{number}`\nAmount: {amount} BDT", parse_mode="Markdown")

def process_deposit(message):
    txn_data = message.text
    bot.send_message(message.chat.id, "✅ Deposit request sent to admin for verification.")
    bot.send_message(ADMIN_ID, f"🚨 **New Deposit Request**\n\nUser: `{message.chat.id}`\nDetails: `{txn_data}`", parse_mode="Markdown")

def process_broadcast(message):
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    success = 0
    for u in users:
        try:
            bot.send_message(u[0], f"📢 **Announcement**\n\n{message.text}", parse_mode="Markdown")
            success += 1
        except:
            pass
    bot.send_message(ADMIN_ID, f"✅ Broadcast sent to {success} users.")

print("🚀 Bot is running...")
bot.infinity_polling()
