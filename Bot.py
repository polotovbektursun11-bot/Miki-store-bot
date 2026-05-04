import telebot
from telebot import types
import requests
import time
import threading

TOKEN = "8600943961:AAH4ftHZ8rWkQEGFS6YGOn2qmMCdjsZQ8P0"
bot = telebot.TeleBot(TOKEN)

# 👑 ADMINS (2 админа)
ADMINS = [6618897334, 1393440847]

SELLER = "@Miki_old01"
SUPPORT = "@zangetsua"
REVIEWS = "@otziv_miki01"

# ₿ CRYPTO
CRYPTO_TOKEN = "577165:AAl0hIw8zScrYACIMhxNOTjEPKn7JAV4fGT"
CRYPTO_API = "https://pay.crypt.bot/api"

# =====================
# 📦 DATA
# =====================
users = {}
cart = {}
logs = {}

products = {
    "безумные": {"rub": 500, "usd": 4.5},
    "индивид": {"rub": 350, "usd": 3},
    "вип": {"rub": 200, "usd": 2},
    "просто топ": {"rub": 100, "usd": 1},
    "обычные": {"rub": 50, "usd": 0.5}
}

# =====================
# 🧠 SAFE USER
# =====================
def get_user(uid):
    if uid not in users:
        users[uid] = {"buy": 0, "invoice": None}
    return users[uid]

def is_admin(uid):
    return uid in ADMINS

# =====================
# 🏠 START
# =====================
@bot.message_handler(commands=['start'])
def start(m):
    get_user(m.from_user.id)

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛒 Товары", "🧺 Корзина")
    kb.add("👤 Профиль", "⭐ Отзывы")
    kb.add("📞 Поддержка")

    if is_admin(m.from_user.id):
        kb.add("👑 Админ")

    bot.send_message(m.chat.id, "🛍 MIKI SHOP PRO", reply_markup=kb)

# =====================
# 🛒 SHOP (НОВЫЙ UI)
# =====================
@bot.message_handler(func=lambda m: m.text == "🛒 Товары")
def shop(m):
    kb = types.InlineKeyboardMarkup()

    for name, price in products.items():
        kb.add(types.InlineKeyboardButton(
            f"{name} — {price['rub']}₽",
            callback_data=f"item_{name}"
        ))

    bot.send_message(m.chat.id, "📦 Выбери товар:", reply_markup=kb)

# =====================
# 📦 ITEM MENU (НОВЫЙ)
# =====================
@bot.callback_query_handler(func=lambda c: c.data.startswith("item_"))
def item_menu(c):
    uid = c.from_user.id
    item = c.data.split("_")[1]

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("➕ В корзину", callback_data=f"add_{item}"))
    kb.add(types.InlineKeyboardButton("💳 Купить сразу", callback_data=f"buy_{item}"))

    bot.send_message(c.message.chat.id, f"📦 {item}", reply_markup=kb)

# =====================
# ➕ ADD CART
# =====================
@bot.callback_query_handler(func=lambda c: c.data.startswith("add_"))
def add(c):
    uid = c.from_user.id
    item = c.data.split("_")[1]

    cart.setdefault(uid, []).append(item)
    bot.send_message(c.message.chat.id, f"➕ Добавлено в корзину: {item}")

# =====================
# 💳 BUY DIRECT
# =====================
@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def buy_direct(c):
    uid = c.from_user.id
    item = c.data.split("_")[1]

    cart[uid] = [item]
    show_pay(c.message, uid)

# =====================
# 🧺 CART
# =====================
@bot.message_handler(func=lambda m: m.text == "🧺 Корзина")
def show_cart(m):
    uid = m.from_user.id
    items = cart.get(uid, [])

    if not items:
        return bot.send_message(m.chat.id, "🧺 Пусто")

    total = sum(products[i]["rub"] for i in items)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💳 Оплатить", callback_data="pay"))

    bot.send_message(m.chat.id,
        f"🧺 Заказ: {items}\n💰 {total}₽",
        reply_markup=kb
    )

# =====================
# 💳 PAY MENU
# =====================
@bot.callback_query_handler(func=lambda c: c.data == "pay")
def pay(c):
    show_pay(c.message, c.from_user.id)

def show_pay(msg, uid):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💳 СБЕР/ЮМАНИ", callback_data="rub"))
    kb.add(types.InlineKeyboardButton("⭐ STARS", callback_data="stars"))
    kb.add(types.InlineKeyboardButton("₿ CRYPTO", callback_data="crypto"))

    bot.send_message(msg.chat.id, "💰 Выбери оплату:", reply_markup=kb)

# =====================
# 💳 RUB
# =====================
@bot.callback_query_handler(func=lambda c: c.data == "rub")
def rub(c):
    bot.send_message(c.message.chat.id,
        "💳 Реквизиты:\n"
        "Сбер: 2202202360594943\n"
        "Юмани: 4100118566817343\n"
        "Получатель: Ахмед Ц\n\n"
        "📸 Отправь чек"
    )

# =====================
# ⭐ STARS
# =====================
@bot.callback_query_handler(func=lambda c: c.data == "stars")
def stars(c):
    bot.send_message(c.message.chat.id, "⭐ Оплата через Stars → @Miki_old01")

# =====================
# ₿ CRYPTO
# =====================
def create_invoice(amount, uid):
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}

    data = {
        "asset": "USDT",
        "amount": amount,
        "description": f"MIKI SHOP {uid}"
    }

    r = requests.post(f"{CRYPTO_API}/createInvoice", headers=headers, data=data)
    return r.json()

@bot.callback_query_handler(func=lambda c: c.data == "crypto")
def crypto(c):
    uid = c.from_user.id
    user = get_user(uid)

    items = cart.get(uid, [])
    if not items:
        return bot.send_message(c.message.chat.id, "🧺 Пусто")

    total = sum(products[i]["usd"] for i in items)

    inv = create_invoice(total, uid)

    pay_url = inv["result"]["pay_url"]
    user["invoice"] = inv["result"]["invoice_id"]

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💰 ОПЛАТИТЬ", url=pay_url))

    bot.send_message(c.message.chat.id,
        f"₿ CryptoBot: {total}$",
        reply_markup=kb
    )

# =====================
# 🔍 CHECK LOOP
# =====================
def check_invoice(inv_id):
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}

    r = requests.get(
        f"{CRYPTO_API}/getInvoices?invoice_ids={inv_id}",
        headers=headers
    )
    return r.json()["result"]["items"][0]["status"]

def auto_check():
    while True:
        for uid in list(users.keys()):
            user = get_user(uid)

            if user.get("invoice"):
                try:
                    status = check_invoice(user["invoice"])

                    if status == "paid":
                        bot.send_message(uid, "✅ ОПЛАТА ПОДТВЕРЖДЕНА\nТовар: " + SELLER)

                        user["buy"] += 1
                        user["invoice"] = None
                        cart[uid] = []
                        logs.append(uid)

                except:
                    pass

        time.sleep(10)

threading.Thread(target=auto_check, daemon=True).start()

# =====================
# 👤 PROFILE FIXED
# =====================
@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(m):
    uid = m.from_user.id
    user = get_user(uid)

    bot.send_message(m.chat.id,
        f"👤 Профиль\nПокупок: {user['buy']}"
    )

# =====================
# 📞 SUPPORT
# =====================
@bot.message_handler(func=lambda m: m.text == "📞 Поддержка")
def support(m):
    bot.send_message(m.chat.id, SUPPORT)

# =====================
# ⭐ REVIEWS
# =====================
@bot.message_handler(func=lambda m: m.text == "⭐ Отзывы")
def review(m):
    bot.send_message(m.chat.id, REVIEWS)

# =====================
# 👑 ADMIN PANEL (ТОЛЬКО АДМИНЫ)
# =====================
@bot.message_handler(func=lambda m: m.text == "👑 Админ")
def admin(m):
    if not is_admin(m.from_user.id):
        return

    bot.send_message(m.chat.id,
        f"👑 ADMIN PANEL\n"
        f"Users: {len(users)}\n"
        f"Logs: {len(logs)}"
    )

# =====================
# 🚀 RUN
# =====================
print("MIKI SHOP PRO ULTIMATE RUNNING...")
bot.polling(none_stop=True)
