import asyncio, json, os, re
from pathlib import Path

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])          # ваш Telegram ID (узнать у @userinfobot)
PORT = int(os.environ.get("PORT", "8080"))
SLOTS = 7                                         # число кнопок «Открыть»
NAMES = ["Вб дарит бесплатно", "Трендовый маникюр", "Рекко", "Блогеры",
         "Общение", "Гороскоп на каждый день", "Новинки кино"]
DATA = Path(os.environ.get("DATA_FILE", "links.json"))
YT = re.compile(r"^https?://(www\.|m\.)?(youtube\.com|youtu\.be)/\S+$", re.I)

def load():
    try:
        d = json.loads(DATA.read_text("utf-8"))
        return (d + [""] * SLOTS)[:SLOTS]
    except Exception:
        return [""] * SLOTS

def save(links):
    DATA.write_text(json.dumps(links, ensure_ascii=False), "utf-8")

links = load()
waiting = {}  # admin_id -> номер кнопки (0..6) или "all"

bot = Bot(TOKEN)
dp = Dispatcher()

def panel():
    rows = [[InlineKeyboardButton(
        text=f"{i+1}. {NAMES[i]} {'✅' if links[i] else '▫️'}", callback_data=f"set:{i}")]
        for i in range(SLOTS)]
    rows.append([InlineKeyboardButton(text="🎬 Одна ссылка для всех кнопок", callback_data="set:all")])
    rows.append([InlineKeyboardButton(text="🧹 Сбросить все", callback_data="reset")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def is_admin(uid): return uid == ADMIN_ID

@dp.message(Command("start", "panel"))
async def start(m: Message):
    if not is_admin(m.from_user.id):
        return
    waiting.pop(m.from_user.id, None)
    await m.answer("Панель ссылок. Выберите кнопку, затем отправьте ссылку на ролик с YouTube.", reply_markup=panel())

@dp.callback_query(F.data.startswith("set:"))
async def pick(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return await c.answer()
    k = c.data.split(":")[1]
    waiting[c.from_user.id] = "all" if k == "all" else int(k)
    cur = "" if k == "all" or not links[int(k)] else f"\nСейчас: {links[int(k)]}"
    await c.message.answer("Отправьте ссылку на ролик с YouTube." + cur)
    await c.answer()

@dp.callback_query(F.data == "reset")
async def reset(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return await c.answer()
    links[:] = [""] * SLOTS; save(links)
    await c.message.edit_reply_markup(reply_markup=panel())
    await c.answer("Сброшено")

@dp.message(F.text)
async def got_link(m: Message):
    if not is_admin(m.from_user.id):
        return
    target = waiting.get(m.from_user.id)
    if target is None:
        return await m.answer("Сначала выберите кнопку: /panel")
    url = m.text.strip()
    if not YT.match(url):
        return await m.answer("Это не похоже на ссылку YouTube. Пришлите ещё раз.")
    if target == "all":
        links[:] = [url] * SLOTS
    else:
        links[target] = url
    save(links); waiting.pop(m.from_user.id, None)
    await m.answer("Готово ✅", reply_markup=panel())

# ---- API для мини-приложения ----
@web.middleware
async def cors(request, handler):
    resp = web.Response(status=204) if request.method == "OPTIONS" else await handler(request)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "*"
    return resp

async def api_links(_):
    return web.json_response({"links": links})

async def main():
    app = web.Application(middlewares=[cors])
    app.router.add_get("/api/links", api_links)
    app.router.add_get("/", lambda r: web.FileResponse(Path(__file__).with_name("channel_hub.html")))
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
