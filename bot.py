<<<<<<< HEAD
import os
import logging
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================== TOKEN ==================
API_TOKEN = os.environ.get("API_TOKEN")  # Environment variable orqali olinadi

# ================== LOG ==================
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ================== DATABASE ==================
conn = sqlite3.connect("murojaatlar.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS murojaatlar(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT,
    sana TEXT,
    fish TEXT,
    tel TEXT,
    manzil TEXT,
    turi TEXT,
    matn TEXT,
    holat TEXT,
    user_id INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS admins(
    id INTEGER PRIMARY KEY,
    username TEXT,
    password TEXT
)
""")

ADMIN_LOGIN = "xujankuloff"
ADMIN_PASSWORD = "121478"

cursor.execute("SELECT * FROM admins WHERE username=?", (ADMIN_LOGIN,))
if not cursor.fetchone():
    cursor.execute(
        "INSERT INTO admins VALUES (1,?,?)",
        (ADMIN_LOGIN, ADMIN_PASSWORD)
    )
conn.commit()

# ================== STATES ==================
class UserState(StatesGroup):
    fish = State()
    tel = State()
    manzil = State()
    turi = State()
    matn = State()
    confirm = State()

class AdminLogin(StatesGroup):
    login = State()
    password = State()

# ================== KEYBOARDS ==================
def main_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📝 Murojaat yuborish", callback_data="new"))
    kb.add(InlineKeyboardButton("📊 Murojaatlarim", callback_data="my"))
    return kb

def confirm_kb():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ Tasdiqlash", callback_data="yes"),
        InlineKeyboardButton("❌ Bekor qilish", callback_data="no")
    )
    return kb

def turi_kb():
    kb = InlineKeyboardMarkup()
    for t in ["Suv", "Elektr", "Yo‘l", "Yer", "Ijtimoiy", "Boshqa"]:
        kb.add(InlineKeyboardButton(t, callback_data=f"type_{t}"))
    return kb

# ================== START ==================
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    await m.answer(
        "📨 Navbahor tuman hokimligiga murojaatlar botiga xush kelibsiz",
        reply_markup=main_kb()
    )

# ================== USER FLOW ==================
@dp.callback_query_handler(text="new")
async def new_murojaat(c: types.CallbackQuery):
    await c.message.answer("👤 F.I.Sh ni kiriting:")
    await UserState.fish.set()

@dp.message_handler(state=UserState.fish)
async def fish(m: types.Message, state: FSMContext):
    await state.update_data(fish=m.text)
    await m.answer("📞 Telefon raqamingizni kiriting:")
    await UserState.tel.set()

@dp.message_handler(state=UserState.tel)
async def tel(m: types.Message, state: FSMContext):
    await state.update_data(tel=m.text)
    await m.answer("🏠 Manzilingizni kiriting:")
    await UserState.manzil.set()

@dp.message_handler(state=UserState.manzil)
async def manzil(m: types.Message, state: FSMContext):
    await state.update_data(manzil=m.text)
    await m.answer("🗂 Murojaat turini tanlang:", reply_markup=turi_kb())
    await UserState.turi.set()

@dp.callback_query_handler(lambda c: c.data.startswith("type_"), state=UserState.turi)
async def turi(c: types.CallbackQuery, state: FSMContext):
    await state.update_data(turi=c.data.replace("type_", ""))
    await c.message.answer("✍️ Murojaat matnini yozing:")
    await UserState.matn.set()

@dp.message_handler(state=UserState.matn)
async def matn(m: types.Message, state: FSMContext):
    await state.update_data(matn=m.text)
    await m.answer("✅ Tasdiqlaysizmi?", reply_markup=confirm_kb())
    await UserState.confirm.set()

@dp.callback_query_handler(state=UserState.confirm)
async def confirm(c: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if c.data == "yes":
        n = cursor.execute("SELECT COUNT(*) FROM murojaatlar").fetchone()[0] + 1
        code = f"01-35-b{n}"
        cursor.execute("""
        INSERT INTO murojaatlar
        (code, sana, fish, tel, manzil, turi, matn, holat, user_id)
        VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            code,
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            data["fish"],
            data["tel"],
            data["manzil"],
            data["turi"],
            data["matn"],
            "Qabul qilindi",
            c.from_user.id
        ))
        conn.commit()
        await c.message.edit_text(
            f"✅ Murojaatingiz qabul qilindi!\n📌 Raqam: {code}",
            reply_markup=main_kb()
        )
    else:
        await c.message.edit_text("❌ Murojaat bekor qilindi", reply_markup=main_kb())
    await state.finish()

@dp.callback_query_handler(text="my")
async def my(c: types.CallbackQuery):
    rows = cursor.execute(
        "SELECT code, holat FROM murojaatlar WHERE user_id=?",
        (c.from_user.id,)
    ).fetchall()

    if not rows:
        await c.message.edit_text("📭 Sizda murojaatlar yo‘q", reply_markup=main_kb())
        return

    text = "📊 Sizning murojaatlaringiz:\n\n"
    for r in rows:
        text += f"📌 {r[0]} — {r[1]}\n"
    await c.message.edit_text(text, reply_markup=main_kb())

# ================== ADMIN ==================
@dp.message_handler(commands=["admin"])
async def admin_start(m: types.Message):
    await m.answer("👤 Admin loginini kiriting:")
    await AdminLogin.login.set()

@dp.message_handler(state=AdminLogin.login)
async def admin_login(m: types.Message, state: FSMContext):
    await state.update_data(login=m.text)
    await m.answer("🔐 Parolni kiriting:")
    await AdminLogin.password.set()

@dp.message_handler(state=AdminLogin.password)
async def admin_pass(m: types.Message, state: FSMContext):
    data = await state.get_data()
    admin = cursor.execute(
        "SELECT * FROM admins WHERE username=? AND password=?",
        (data["login"], m.text)
    ).fetchone()

    if admin:
        rows = cursor.execute(
            "SELECT code, fish, tel, turi, holat FROM murojaatlar"
        ).fetchall()

        if not rows:
            await m.answer("📭 Murojaatlar yo‘q")
        else:
            text = "📋 Barcha murojaatlar:\n\n"
            for r in rows:
                text += f"{r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]}\n"
            await m.answer(text)
    else:
        await m.answer("❌ Login yoki parol noto‘g‘ri")

    await state.finish()

# ================== RUN ==================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
=======
import logging
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================== TOKEN ==================
API_TOKEN = "8277225125:AAESYsPkN4JBdL9jGzja4u2WbrMGEUc3aS4"

# ================== LOG ==================
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ================== DATABASE ==================
conn = sqlite3.connect("murojaatlar.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS murojaatlar(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT,
    sana TEXT,
    fish TEXT,
    tel TEXT,
    manzil TEXT,
    turi TEXT,
    matn TEXT,
    holat TEXT,
    user_id INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS admins(
    id INTEGER PRIMARY KEY,
    username TEXT,
    password TEXT
)
""")

ADMIN_LOGIN = "xujankuloff"
ADMIN_PASSWORD = "121478"

cursor.execute("SELECT * FROM admins WHERE username=?", (ADMIN_LOGIN,))
if not cursor.fetchone():
    cursor.execute(
        "INSERT INTO admins VALUES (1,?,?)",
        (ADMIN_LOGIN, ADMIN_PASSWORD)
    )
conn.commit()

# ================== STATES ==================
class UserState(StatesGroup):
    fish = State()
    tel = State()
    manzil = State()
    turi = State()
    matn = State()
    confirm = State()

class AdminLogin(StatesGroup):
    login = State()
    password = State()

# ================== KEYBOARDS ==================
def main_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📝 Murojaat yuborish", callback_data="new"))
    kb.add(InlineKeyboardButton("📊 Murojaatlarim", callback_data="my"))
    return kb

def confirm_kb():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ Tasdiqlash", callback_data="yes"),
        InlineKeyboardButton("❌ Bekor qilish", callback_data="no")
    )
    return kb

def turi_kb():
    kb = InlineKeyboardMarkup()
    for t in ["Suv", "Elektr", "Yo‘l", "Yer", "Ijtimoiy", "Boshqa"]:
        kb.add(InlineKeyboardButton(t, callback_data=f"type_{t}"))
    return kb

# ================== START ==================
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    await m.answer(
        "📨 Navbahor tuman hokimligiga murojaatlar botiga xush kelibsiz",
        reply_markup=main_kb()
    )

# ================== USER FLOW ==================
@dp.callback_query_handler(text="new")
async def new_murojaat(c: types.CallbackQuery):
    await c.message.answer("👤 F.I.Sh ni kiriting:")
    await UserState.fish.set()

@dp.message_handler(state=UserState.fish)
async def fish(m: types.Message, state: FSMContext):
    await state.update_data(fish=m.text)
    await m.answer("📞 Telefon raqamingizni kiriting:")
    await UserState.tel.set()

@dp.message_handler(state=UserState.tel)
async def tel(m: types.Message, state: FSMContext):
    await state.update_data(tel=m.text)
    await m.answer("🏠 Manzilingizni kiriting:")
    await UserState.manzil.set()

@dp.message_handler(state=UserState.manzil)
async def manzil(m: types.Message, state: FSMContext):
    await state.update_data(manzil=m.text)
    await m.answer("🗂 Murojaat turini tanlang:", reply_markup=turi_kb())
    await UserState.turi.set()

@dp.callback_query_handler(lambda c: c.data.startswith("type_"), state=UserState.turi)
async def turi(c: types.CallbackQuery, state: FSMContext):
    await state.update_data(turi=c.data.replace("type_", ""))
    await c.message.answer("✍️ Murojaat matnini yozing:")
    await UserState.matn.set()

@dp.message_handler(state=UserState.matn)
async def matn(m: types.Message, state: FSMContext):
    await state.update_data(matn=m.text)
    await m.answer("✅ Tasdiqlaysizmi?", reply_markup=confirm_kb())
    await UserState.confirm.set()

@dp.callback_query_handler(state=UserState.confirm)
async def confirm(c: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if c.data == "yes":
        n = cursor.execute("SELECT COUNT(*) FROM murojaatlar").fetchone()[0] + 1
        code = f"01-35-b{n}"
        cursor.execute("""
        INSERT INTO murojaatlar
        (code, sana, fish, tel, manzil, turi, matn, holat, user_id)
        VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            code,
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            data["fish"],
            data["tel"],
            data["manzil"],
            data["turi"],
            data["matn"],
            "Qabul qilindi",
            c.from_user.id
        ))
        conn.commit()
        await c.message.edit_text(
            f"✅ Murojaatingiz qabul qilindi!\n📌 Raqam: {code}",
            reply_markup=main_kb()
        )
    else:
        await c.message.edit_text("❌ Murojaat bekor qilindi", reply_markup=main_kb())
    await state.finish()

@dp.callback_query_handler(text="my")
async def my(c: types.CallbackQuery):
    rows = cursor.execute(
        "SELECT code, holat FROM murojaatlar WHERE user_id=?",
        (c.from_user.id,)
    ).fetchall()

    if not rows:
        await c.message.edit_text("📭 Sizda murojaatlar yo‘q", reply_markup=main_kb())
        return

    text = "📊 Sizning murojaatlaringiz:\n\n"
    for r in rows:
        text += f"📌 {r[0]} — {r[1]}\n"
    await c.message.edit_text(text, reply_markup=main_kb())

# ================== ADMIN ==================
@dp.message_handler(commands=["admin"])
async def admin_start(m: types.Message):
    await m.answer("👤 Admin loginini kiriting:")
    await AdminLogin.login.set()

@dp.message_handler(state=AdminLogin.login)
async def admin_login(m: types.Message, state: FSMContext):
    await state.update_data(login=m.text)
    await m.answer("🔐 Parolni kiriting:")
    await AdminLogin.password.set()

@dp.message_handler(state=AdminLogin.password)
async def admin_pass(m: types.Message, state: FSMContext):
    data = await state.get_data()
    admin = cursor.execute(
        "SELECT * FROM admins WHERE username=? AND password=?",
        (data["login"], m.text)
    ).fetchone()

    if admin:
        rows = cursor.execute(
            "SELECT code, fish, tel, turi, holat FROM murojaatlar"
        ).fetchall()

        if not rows:
            await m.answer("📭 Murojaatlar yo‘q")
        else:
            text = "📋 Barcha murojaatlar:\n\n"
            for r in rows:
                text += f"{r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]}\n"
            await m.answer(text)
    else:
        await m.answer("❌ Login yoki parol noto‘g‘ri")

    await state.finish()

# ================== RUN ==================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
>>>>>>> ebb930db40e9db03ffbd76e92322f770cb094540
