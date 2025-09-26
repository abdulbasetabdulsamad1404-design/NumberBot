# bot_full_manage_final.py — Aiogram v2، کامل، دکمه‌ها، مدیریت مخاطب، ذخیره در اکسل
import logging
import threading
import time
import os
import pandas as pd
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

# ---------------- تنظیمات ----------------
TOKEN = "8181744010:AAHxGNoR5lyHctBz2LhRmIZ5scER23Ic4tk"
ADMIN_ID = 7755177091
DB_FILE = "contacts.xlsx"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ---------------- حالت‌ها ----------------
class Form(StatesGroup):
    waiting_for_name = State()
    waiting_for_tag = State()
    waiting_for_add_name = State()
    waiting_for_add_numbers = State()
    waiting_for_add_address = State()
    waiting_for_add_label = State()
    waiting_for_edit_select = State()
    waiting_for_edit_field = State()
    waiting_for_edit_value = State()
    waiting_for_delete = State()
    waiting_for_excel = State()

# ---------------- داده‌ها ----------------
contacts_df = pd.DataFrame(columns=["name", "phone_numbers", "address", "label"])

def load_contacts():
    global contacts_df
    if os.path.exists(DB_FILE):
        try:
            contacts_df = pd.read_excel(DB_FILE)
            for c in ["name", "phone_numbers", "address", "label"]:
                if c not in contacts_df.columns:
                    contacts_df[c] = ""
        except:
            contacts_df = pd.DataFrame(columns=["name","phone_numbers","address","label"])
    else:
        contacts_df.to_excel(DB_FILE, index=False)

def save_contacts():
    global contacts_df
    contacts_df.to_excel(DB_FILE, index=False)

# ---------------- رفرش خودکار اکسل ----------------
def excel_watcher(poll_interval=3):
    last_mtime = None
    while True:
        try:
            if os.path.exists(DB_FILE):
                mtime = os.path.getmtime(DB_FILE)
                if last_mtime is None or mtime != last_mtime:
                    logging.info("تغییر در فایل اکسل دیده شد — بارگذاری مجدد")
                    load_contacts()
                    last_mtime = mtime
        except:
            logging.exception("خطا در اکسل واچر")
        time.sleep(poll_interval)

# ---------------- کیبوردها ----------------
user_kb = ReplyKeyboardMarkup(resize_keyboard=True)
user_kb.add(KeyboardButton("جستجوی مخاطب 🔍"))
user_kb.add(KeyboardButton("جستجوی برچسب 🏷"))

admin_kb = ReplyKeyboardMarkup(resize_keyboard=True)
admin_kb.add(
    KeyboardButton("افزودن مخاطب ➕"),
    KeyboardButton("ویرایش مخاطب ✏️"),
    KeyboardButton("حذف مخاطب 🗑"),
)
admin_kb.add(
    KeyboardButton("ارسال فایل اکسل 📁"),
    KeyboardButton("دریافت فایل اکسل 📤"),
)
admin_kb.add(
    KeyboardButton("جستجوی مخاطب 🔍"),
    KeyboardButton("جستجوی برچسب 🏷"),
)

# ---------------- استارت ----------------
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    load_contacts()
    if message.from_user.id == ADMIN_ID:
        await message.reply("سلام مدیر 👋\nبه ربات شماره‌یاب خوش آمدید.", reply_markup=admin_kb)
    else:
        await message.reply(
            "سلام 😃\nبه ربات شماره‌یاب خوش آمدید.\n"
            "از منوی زیر می‌توانید جستجوی مخاطب یا برچسب را انجام دهید.",
            reply_markup=user_kb
        )
        await Form.waiting_for_name.set()

# ---------------- نمایش اطلاعات مخاطب ----------------
async def send_contact_info(message: types.Message, df):
    for _, row in df.iterrows():
        phones = str(row.get("phone_numbers","")).strip()
        phone_lines = phones.split("|") if phones else ["-"]
        phone_text = "\n".join([f"📞 <a href='tel:{p.strip()}'>{p.strip()}</a>" for p in phone_lines if p.strip()!=""])
        if phone_text == "":
            phone_text = "-"
        info = (
            f"✅ مخاطب یافت شد\n\n"
            f"👤 نام: {row.get('name', '-')}\n"
            f"{phone_text}\n"
            f"📍 آدرس: {row.get('address', '-')}\n"
            f"🏷 برچسب: {row.get('label', '-')}"
        )
        await message.reply(info, parse_mode="HTML")

# ---------------- جستجوی نام ----------------
@dp.message_handler(lambda m: m.text=="جستجوی مخاطب 🔍", state="*")
async def prompt_name_search(message: types.Message):
    await message.reply("لطفا نام مخاطب را وارد کنید:")
    await Form.waiting_for_name.set()

@dp.message_handler(state=Form.waiting_for_name)
async def handle_search_name(message: types.Message, state: FSMContext):
    load_contacts()
    global contacts_df
    query = message.text.strip()
    if query == "":
        await message.reply("لطفا یک اسم وارد کنید.")
        return
    df = contacts_df
    if df.empty:
        await message.reply("❌ دیتابیسی موجود نیست.")
        return
    result = df[df["name"].str.contains(query, case=False, na=False)]
    if result.empty:
        await message.reply("❌ مخاطب یافت نشد")
        return
    await send_contact_info(message, result)
    await state.finish()

# ---------------- جستجوی برچسب ----------------
@dp.message_handler(lambda m: m.text=="جستجوی برچسب 🏷", state="*")
async def prompt_tag_search(message: types.Message):
    await message.reply("لطفا برچسب مورد نظر را وارد کنید:")
    await Form.waiting_for_tag.set()

@dp.message_handler(state=Form.waiting_for_tag)
async def handle_search_tag(message: types.Message, state: FSMContext):
    load_contacts()
    global contacts_df
    query = message.text.strip()
    if query == "":
        await message.reply("لطفا یک برچسب وارد کنید.")
        return
    df = contacts_df
    if df.empty:
        await message.reply("❌ دیتابیسی موجود نیست.")
        return
    result = df[df["label"].str.contains(query, case=False, na=False)]
    if result.empty:
        await message.reply("❌ مخاطب یافت نشد")
        return
    await send_contact_info(message, result)
    await state.finish()

# ---------------- بخش مدیریت کامل ----------------
# افزودن مخاطب
@dp.message_handler(Text(equals="افزودن مخاطب ➕"))
async def start_add_contact(message: types.Message):
    await message.reply("لطفا نام مخاطب را وارد کنید:")
    await Form.waiting_for_add_name.set()

@dp.message_handler(state=Form.waiting_for_add_name)
async def add_contact_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.reply("شماره‌ها را وارد کنید (در صورت چند شماره با | جدا کنید):")
    await Form.waiting_for_add_numbers.set()

@dp.message_handler(state=Form.waiting_for_add_numbers)
async def add_contact_numbers(message: types.Message, state: FSMContext):
    await state.update_data(phone_numbers=message.text.strip())
    await message.reply("آدرس را وارد کنید:")
    await Form.waiting_for_add_address.set()

@dp.message_handler(state=Form.waiting_for_add_address)
async def add_contact_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    await message.reply("برچسب را وارد کنید:")
    await Form.waiting_for_add_label.set()

@dp.message_handler(state=Form.waiting_for_add_label)
async def add_contact_label(message: types.Message, state: FSMContext):
    data = await state.get_data()
    new_contact = {
        "name": data.get("name"),
        "phone_numbers": data.get("phone_numbers"),
        "address": data.get("address"),
        "label": data.get("label")
    }
    global contacts_df
    contacts_df = pd.concat([contacts_df, pd.DataFrame([new_contact])], ignore_index=True)
    save_contacts()
    await message.reply("✅ مخاطب اضافه شد.", reply_markup=admin_kb)
    await state.finish()

# ویرایش مخاطب
@dp.message_handler(Text(equals="ویرایش مخاطب ✏️"))
async def start_edit_contact(message: types.Message):
    await message.reply("لطفا نام مخاطب برای ویرایش وارد کنید:")
    await Form.waiting_for_edit_select.set()

@dp.message_handler(state=Form.waiting_for_edit_select)
async def edit_select(message: types.Message, state: FSMContext):
    global contacts_df
    name = message.text.strip()
    df = contacts_df[contacts_df["name"].str.contains(name, case=False, na=False)]
    if df.empty:
        await message.reply("❌ مخاطب یافت نشد.")
        await state.finish()
        return
    await state.update_data(edit_name=name)
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("نام", "شماره‌ها", "آدرس", "برچسب")
    await message.reply("کدام فیلد را می‌خواهید ویرایش کنید؟", reply_markup=kb)
    await Form.waiting_for_edit_field.set()

@dp.message_handler(state=Form.waiting_for_edit_field)
async def edit_field_select(message: types.Message, state: FSMContext):
    field_map = {"نام": "name", "شماره‌ها": "phone_numbers", "آدرس": "address", "برچسب": "label"}
    field = field_map.get(message.text.strip())
    if not field:
        await message.reply("❌ انتخاب نامعتبر.")
        return
    await state.update_data(edit_field=field)
    await message.reply(f"مقدار جدید برای {message.text.strip()} را وارد کنید:")
    await Form.waiting_for_edit_value.set()

@dp.message_handler(state=Form.waiting_for_edit_value)
async def edit_value_set(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data.get("edit_name")
    field = data.get("edit_field")
    global contacts_df
    idx = contacts_df[contacts_df["name"].str.contains(name, case=False, na=False)].index
    if not idx.empty:
        contacts_df.loc[idx, field] = message.text.strip()
        save_contacts()
        await message.reply("✅ ویرایش انجام شد.", reply_markup=admin_kb)
    else:
        await message.reply("❌ مخاطب یافت نشد.")
    await state.finish()

# حذف مخاطب
@dp.message_handler(Text(equals="حذف مخاطب 🗑"))
async def start_delete_contact(message: types.Message):
    await message.reply("لطفا نام مخاطب را برای حذف وارد کنید:")
    await Form.waiting_for_delete.set()

@dp.message_handler(state=Form.waiting_for_delete)
async def delete_contact(message: types.Message, state: FSMContext):
    global contacts_df
    name = message.text.strip()
    df = contacts_df[contacts_df["name"].str.contains(name, case=False, na=False)]
    if df.empty:
        await message.reply("❌ مخاطب یافت نشد.")
    else:
        contacts_df.drop(df.index, inplace=True)
        save_contacts()
        await message.reply("✅ مخاطب حذف شد.", reply_markup=admin_kb)
    await state.finish()

# مدیریت فایل اکسل
@dp.message_handler(Text(equals="ارسال فایل اکسل 📁"))
async def ask_upload_excel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("❌ شما دسترسی ندارید.")
        return
    await message.reply("لطفا فایل اکسل (.xlsx) را ارسال کنید.")
    await Form.waiting_for_excel.set()

@dp.message_handler(content_types=types.ContentType.DOCUMENT, state=Form.waiting_for_excel)
async def handle_upload_excel(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    doc = message.document
    if not doc.file_name.lower().endswith(".xlsx"):
        await message.reply("❌ فرمت غیرمجاز. لطفا فایل با پسوند .xlsx ارسال کنید.")
        await state.finish()
        return
    try:
        await doc.download(destination_file=DB_FILE)
        load_contacts()
        await message.reply("✅ فایل اکسل دریافت شد و اطلاعات به‌روز شد.", reply_markup=admin_kb)
    except:
        await message.reply("❌ خطا در دریافت فایل.")
    await state.finish()

@dp.message_handler(Text(equals="دریافت فایل اکسل 📤"))
async def send_excel_file(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("❌ شما دسترسی ندارید.")
        return
    if not os.path.exists(DB_FILE):
        await message.reply("❌ فایل اکسل موجود نیست.")
        return
    await message.reply_document(open(DB_FILE, "rb"))

# ---------------- اجرای ربات ----------------
if __name__ == "__main__":
    load_contacts()
    watcher_thread = threading.Thread(target=excel_watcher, args=(3,), daemon=True)
    watcher_thread.start()
    executor.start_polling(dp, skip_updates=True)