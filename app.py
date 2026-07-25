import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime
from typing import Optional
import threading
import asyncio
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import secrets

# ============== КОНФИГУРАЦИЯ ==============
TOKEN = os.getenv("BOT_TOKEN")
DEVELOPER_IDS = [123456789012345678]  # Замените на ваш Discord ID
SERVER_INVITE = "https://discord.gg/hFtkGD9UhU"
BOT_ACTIVITY_TEXT = "Регистрация персонажей"
WEB_PORT = 3000

# Админка
ADMIN_LOGIN = "LOST-SPARK-TTP"
ADMIN_PASSWORD = "A32DSAX-D3W22X-DWLVM3"
SECRET_KEY = secrets.token_hex(32)

# Категории по умолчанию
DEFAULT_CATEGORIES = [
    {"id": "highest", "name": "Высший состав", "color": "#FFD700"},
    {"id": "sponsor", "name": "Спонсорка", "color": "#9B59B6"},
    {"id": "helper", "name": "Хелперский состав", "color": "#3498DB"},
    {"id": "middle", "name": "Средний состав", "color": "#2ECC71"},
    {"id": "junior", "name": "Младший состав", "color": "#95A5A6"}
]

if not TOKEN:
    raise ValueError("❌ Переменная окружения BOT_TOKEN не установлена!")

# ============== БАЗА ДАННЫХ (JSON) ==============
DATA_FILE = "bot_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "categories" not in data:
                data["categories"] = DEFAULT_CATEGORIES
            return data
    return {
        "guilds": {},
        "registered_users": {},
        "logs": [],
        "moderators": [],
        "admins": [],
        "owners": [],
        "categories": DEFAULT_CATEGORIES
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============== FASTAPI ВЕБ-СЕРВЕР ==============
web_app = FastAPI()
web_app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
templates = Jinja2Templates(directory="templates")

@web_app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if not request.session.get("logged_in"):
        return RedirectResponse(url="/login", status_code=302)
    return RedirectResponse(url="/dashboard", status_code=302)

@web_app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})

@web_app.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request, login: str = Form(...), password: str = Form(...)):
    if login == ADMIN_LOGIN and password == ADMIN_PASSWORD:
        request.session["logged_in"] = True
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request, "login.html", {"error": "Неверный логин или пароль"})

@web_app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)

@web_app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not request.session.get("logged_in"):
        return RedirectResponse(url="/login", status_code=302)
    
    data = load_data()
    return templates.TemplateResponse(request, "index.html", {
        "players": data.get("registered_users", {}),
        "categories": data.get("categories", DEFAULT_CATEGORIES)
    })

# API маршруты
@web_app.post("/api/player/category")
async def update_player_category(request: Request):
    if not request.session.get("logged_in"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    body = await request.json()
    data = load_data()
    user_id = body.get("user_id")
    category = body.get("category")
    
    if user_id in data.get("registered_users", {}):
        data["registered_users"][user_id]["category"] = category
        save_data(data)
        return JSONResponse({"success": True})
    
    raise HTTPException(status_code=404, detail="User not found")

@web_app.post("/api/player/delete")
async def delete_player(request: Request):
    if not request.session.get("logged_in"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    body = await request.json()
    data = load_data()
    user_id = body.get("user_id")
    
    if user_id in data.get("registered_users", {}):
        del data["registered_users"][user_id]
        save_data(data)
        return JSONResponse({"success": True})
    
    raise HTTPException(status_code=404, detail="User not found")

@web_app.post("/api/category/add")
async def add_category(request: Request):
    if not request.session.get("logged_in"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    body = await request.json()
    data = load_data()
    name = body.get("name")
    color = body.get("color", "#6366F1")
    
    category_id = name.lower().replace(" ", "_")
    
    for cat in data.get("categories", []):
        if cat["id"] == category_id:
            raise HTTPException(status_code=400, detail="Category already exists")
    
    data["categories"].append({
        "id": category_id,
        "name": name,
        "color": color
    })
    save_data(data)
    return JSONResponse({"success": True})

@web_app.post("/api/category/delete")
async def delete_category(request: Request):
    if not request.session.get("logged_in"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    body = await request.json()
    data = load_data()
    category_id = body.get("category_id")
    
    data["categories"] = [c for c in data.get("categories", []) if c["id"] != category_id]
    
    for user_id in data.get("registered_users", {}):
        if data["registered_users"][user_id].get("category") == category_id:
            data["registered_users"][user_id]["category"] = None
    
    save_data(data)
    return JSONResponse({"success": True})

@web_app.get("/api/players")
async def get_players(request: Request):
    if not request.session.get("logged_in"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    data = load_data()
    return JSONResponse(data.get("registered_users", {}))

def run_web():
    uvicorn.run(web_app, host="0.0.0.0", port=WEB_PORT, log_level="info")

# ============== DISCORD БОТ ==============
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ============== ЛОГИРОВАНИЕ ==============
def add_log(action: str, user, target: str = None, details: str = None):
    data = load_data()
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "user_id": user.id if hasattr(user, 'id') else 0,
        "user_name": str(user),
        "target": target,
        "details": details
    }
    data["logs"].append(log_entry)
    save_data(data)

# ============== ПРОВЕРКИ ПРАВ ==============
def is_developer(user_id: int) -> bool:
    return user_id in DEVELOPER_IDS

def is_owner(user_id: int) -> bool:
    data = load_data()
    return user_id in data.get("owners", []) or is_developer(user_id)

def is_admin(user_id: int) -> bool:
    data = load_data()
    return user_id in data.get("admins", []) or is_owner(user_id)

def is_moderator(user_id: int) -> bool:
    data = load_data()
    return user_id in data.get("moderators", []) or is_admin(user_id)

# ============== МОДАЛЬНЫЕ ОКНА ==============
class RegistrationModal(discord.ui.Modal, title="Регистрация персонажа"):
    nickname = discord.ui.TextInput(
        label="Полный никнейм на сервере",
        placeholder="Введите ваш никнейм...",
        required=True,
        max_length=100
    )
    
    steam_id = discord.ui.TextInput(
        label="STEAM ID",
        placeholder="Например: STEAM_0:1:12345678",
        required=True,
        max_length=50
    )
    
    google_doc = discord.ui.TextInput(
        label="Ссылка на Google Doc с биографией",
        placeholder="https://docs.google.com/...",
        required=True,
        max_length=500
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        guild_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)
        steam_id_value = self.steam_id.value.strip()
        
        if user_id in data.get("registered_users", {}):
            await interaction.response.send_message(
                "❌ Вы уже зарегистрировали персонажа! Повторная регистрация невозможна.",
                ephemeral=True
            )
            return
        
        for uid, info in data.get("registered_users", {}).items():
            if info.get("steam_id", "").lower() == steam_id_value.lower():
                await interaction.response.send_message(
                    "❌ Этот STEAM ID уже зарегистрирован!",
                    ephemeral=True
                )
                return
        
        guild_data = data.get("guilds", {}).get(guild_id, {})
        applications_channel_id = guild_data.get("applications_channel")
        
        if not applications_channel_id:
            await interaction.response.send_message(
                "❌ Канал для заявок не настроен! Обратитесь к администратору.",
                ephemeral=True
            )
            return
        
        applications_channel = bot.get_channel(applications_channel_id)
        if not applications_channel:
            await interaction.response.send_message(
                "❌ Канал для заявок не найден!",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="📋 Новая заявка на регистрацию",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.add_field(name="👤 Пользователь", value=f"{interaction.user.mention} ({interaction.user})", inline=False)
        embed.add_field(name="🎮 Никнейм на сервере", value=self.nickname.value, inline=False)
        embed.add_field(name="🆔 STEAM ID", value=steam_id_value, inline=False)
        embed.add_field(name="📄 Биография", value=f"[Открыть Google Doc]({self.google_doc.value})", inline=False)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"ID пользователя: {interaction.user.id}")
        
        view = ApplicationView(
            user_id=interaction.user.id,
            nickname=self.nickname.value,
            steam_id=steam_id_value,
            google_doc=self.google_doc.value
        )
        
        await applications_channel.send(embed=embed, view=view)
        await interaction.response.send_message(
            "✅ Ваша заявка успешно отправлена на рассмотрение!",
            ephemeral=True
        )
        
        add_log("registration_submitted", interaction.user, steam_id_value, f"Никнейм: {self.nickname.value}")


class RejectReasonModal(discord.ui.Modal, title="Причина отклонения"):
    reason = discord.ui.TextInput(
        label="Укажите причину отклонения",
        placeholder="Введите причину...",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=1000
    )
    
    def __init__(self, user_id: int, steam_id: str, original_message: discord.Message):
        super().__init__()
        self.target_user_id = user_id
        self.steam_id = steam_id
        self.original_message = original_message
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            user = await bot.fetch_user(self.target_user_id)
            embed = discord.Embed(
                title="❌ Заявка отклонена",
                description="Ваша заявка на регистрацию персонажа была отклонена.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.add_field(name="📝 Причина", value=self.reason.value, inline=False)
            embed.add_field(name="👮 Модератор", value=str(interaction.user), inline=False)
            await user.send(embed=embed)
        except:
            pass
        
        embed = self.original_message.embeds[0]
        embed.color = discord.Color.red()
        embed.add_field(name="❌ Статус", value=f"Отклонено модератором {interaction.user.mention}", inline=False)
        embed.add_field(name="📝 Причина", value=self.reason.value, inline=False)
        
        await self.original_message.edit(embed=embed, view=None)
        await interaction.response.send_message("✅ Заявка отклонена, пользователь уведомлен.", ephemeral=True)
        
        add_log("registration_rejected", interaction.user, str(self.target_user_id), f"Причина: {self.reason.value}")


# ============== КНОПКИ ==============
class ApplicationView(discord.ui.View):
    def __init__(self, user_id: int, nickname: str, steam_id: str, google_doc: str):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.nickname = nickname
        self.steam_id = steam_id
        self.google_doc = google_doc
    
    @discord.ui.button(label="✅ Одобрить", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_moderator(interaction.user.id):
            await interaction.response.send_message("❌ У вас нет прав для этого действия!", ephemeral=True)
            return
        
        data = load_data()
        data["registered_users"][str(self.user_id)] = {
            "nickname": self.nickname,
            "steam_id": self.steam_id,
            "google_doc": self.google_doc,
            "registered_at": datetime.now().isoformat(),
            "approved_by": interaction.user.id,
            "category": None
        }
        save_data(data)
        
        try:
            user = await bot.fetch_user(self.user_id)
            embed = discord.Embed(
                title="✅ Заявка одобрена!",
                description="Ваша заявка на регистрацию персонажа была одобрена!",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.add_field(name="🎮 Никнейм", value=self.nickname, inline=False)
            embed.add_field(name="👮 Одобрил", value=str(interaction.user), inline=False)
            await user.send(embed=embed)
        except:
            pass
        
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.add_field(name="✅ Статус", value=f"Одобрено модератором {interaction.user.mention}", inline=False)
        
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("✅ Заявка одобрена, пользователь уведомлен.", ephemeral=True)
        
        add_log("registration_approved", interaction.user, str(self.user_id), f"Steam ID: {self.steam_id}")
    
    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_moderator(interaction.user.id):
            await interaction.response.send_message("❌ У вас нет прав для этого действия!", ephemeral=True)
            return
        
        modal = RejectReasonModal(self.user_id, self.steam_id, interaction.message)
        await interaction.response.send_modal(modal)


# ============== КОМАНДЫ РЕГИСТРАЦИИ ==============
@bot.tree.command(name="registration", description="Открыть форму регистрации персонажа")
async def registration(interaction: discord.Interaction):
    data = load_data()
    
    if str(interaction.user.id) in data.get("registered_users", {}):
        await interaction.response.send_message(
            "❌ Вы уже зарегистрировали персонажа! Повторная регистрация невозможна.",
            ephemeral=True
        )
        return
    
    modal = RegistrationModal()
    await interaction.response.send_modal(modal)


@bot.tree.command(name="регистрация", description="Открыть форму регистрации персонажа")
async def registration_ru(interaction: discord.Interaction):
    await registration.callback(interaction)


# ============== КОМАНДА ИНСТРУКЦИИ ==============
@bot.tree.command(name="send_guide", description="Отправить инструкцию по регистрации")
async def send_guide(interaction: discord.Interaction):
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("❌ Только владельцы могут использовать эту команду!", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    # Embed заголовок
    intro_embed = discord.Embed(
        title="📖 Инструкция по регистрации персонажа",
        description="Следуйте этим простым шагам, чтобы зарегистрировать своего персонажа на сервере.",
        color=discord.Color.blue()
    )
    intro_embed.set_footer(text="Если у вас возникли вопросы — обратитесь к администрации")
    await interaction.channel.send(embed=intro_embed)
    
    # Шаг 1
    step1_embed = discord.Embed(
        title="📌 Шаг 1: Введите команду",
        description=(
            "Введите команду `/registration` или `/регистрация` в любом текстовом канале.\n\n"
            "После этого откроется форма для заполнения данных."
        ),
        color=discord.Color.green()
    )
    if os.path.exists("Shag1.png"):
        file1 = discord.File("Shag1.png", filename="Shag1.png")
        step1_embed.set_image(url="attachment://Shag1.png")
        await interaction.channel.send(embed=step1_embed, file=file1)
    else:
        await interaction.channel.send(embed=step1_embed)
    
    # Шаг 2
    step2_embed = discord.Embed(
        title="📌 Шаг 2: Заполните форму",
        description=(
            "В открывшейся форме заполните следующие поля:\n\n"
            "**1. Полный никнейм на сервере**\n"
            "└ Введите ваш игровой никнейм\n\n"
            "**2. STEAM ID**\n"
            "└ Ваш уникальный Steam идентификатор\n\n"
            "**3. Ссылка на Google Doc с биографией**\n"
            "└ Ссылка на документ с историей вашего персонажа\n\n"
            "После заполнения нажмите кнопку **\"Отправить\"**"
        ),
        color=discord.Color.green()
    )
    if os.path.exists("Shag2.png"):
        file2 = discord.File("Shag2.png", filename="Shag2.png")
        step2_embed.set_image(url="attachment://Shag2.png")
        await interaction.channel.send(embed=step2_embed, file=file2)
    else:
        await interaction.channel.send(embed=step2_embed)
    
    # Финальный embed
    final_embed = discord.Embed(
        title="✅ Готово!",
        description=(
            "После отправки формы ваша заявка будет направлена на рассмотрение модераторам.\n\n"
            "📬 Вы получите уведомление в личные сообщения о результате проверки.\n\n"
            "⏳ Ожидайте — обычно проверка занимает не более 24 часов."
        ),
        color=discord.Color.gold()
    )
    await interaction.channel.send(embed=final_embed)
    
    await interaction.followup.send("✅ Инструкция успешно отправлена!", ephemeral=True)
    add_log("send_guide", interaction.user, str(interaction.channel_id), "Инструкция отправлена")


# ============== КОМАНДЫ НАСТРОЙКИ ==============
@bot.tree.command(name="set_registration_channel", description="Установить канал для команды регистрации")
@app_commands.describe(channel="Канал для регистрации")
async def set_registration_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ Только администраторы могут использовать эту команду!", ephemeral=True)
        return
    
    data = load_data()
    guild_id = str(interaction.guild_id)
    if guild_id not in data["guilds"]:
        data["guilds"][guild_id] = {}
    
    data["guilds"][guild_id]["registration_channel"] = channel.id
    save_data(data)
    
    await interaction.response.send_message(f"✅ Канал для регистрации установлен: {channel.mention}", ephemeral=True)
    add_log("set_registration_channel", interaction.user, str(channel.id), channel.name)


@bot.tree.command(name="set_applications_channel", description="Установить канал для заявок")
@app_commands.describe(channel="Канал для заявок")
async def set_applications_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ Только администраторы могут использовать эту команду!", ephemeral=True)
        return
    
    data = load_data()
    guild_id = str(interaction.guild_id)
    if guild_id not in data["guilds"]:
        data["guilds"][guild_id] = {}
    
    data["guilds"][guild_id]["applications_channel"] = channel.id
    save_data(data)
    
    await interaction.response.send_message(f"✅ Канал для заявок установлен: {channel.mention}", ephemeral=True)
    add_log("set_applications_channel", interaction.user, str(channel.id), channel.name)


# ============== КОМАНДЫ МОДЕРАТОРА ==============
@bot.tree.command(name="delete_character", description="Удалить персонажа по Steam ID")
@app_commands.describe(steam_id="STEAM ID персонажа для удаления")
async def delete_character(interaction: discord.Interaction, steam_id: str):
    if not is_moderator(interaction.user.id):
        await interaction.response.send_message("❌ Только модераторы могут использовать эту команду!", ephemeral=True)
        return
    
    data = load_data()
    user_to_delete = None
    for user_id, info in data.get("registered_users", {}).items():
        if info.get("steam_id", "").lower() == steam_id.lower():
            user_to_delete = user_id
            break
    
    if not user_to_delete:
        await interaction.response.send_message(f"❌ Персонаж с Steam ID `{steam_id}` не найден!", ephemeral=True)
        return
    
    deleted_info = data["registered_users"].pop(user_to_delete)
    save_data(data)
    
    await interaction.response.send_message(
        f"✅ Персонаж удалён!\n"
        f"👤 Никнейм: {deleted_info['nickname']}\n"
        f"🆔 Steam ID: {deleted_info['steam_id']}",
        ephemeral=True
    )
    add_log("character_deleted", interaction.user, steam_id, f"Никнейм: {deleted_info['nickname']}")


# ============== КОМАНДЫ АДМИНИСТРАТОРА ==============
@bot.tree.command(name="add_moderator", description="Выдать права модератора")
@app_commands.describe(user="Пользователь для выдачи прав")
async def add_moderator(interaction: discord.Interaction, user: discord.User):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ Только администраторы могут использовать эту команду!", ephemeral=True)
        return
    
    data = load_data()
    if user.id in data["moderators"]:
        await interaction.response.send_message(f"❌ {user.mention} уже является модератором!", ephemeral=True)
        return
    
    data["moderators"].append(user.id)
    save_data(data)
    
    await interaction.response.send_message(f"✅ {user.mention} теперь модератор!", ephemeral=True)
    add_log("moderator_added", interaction.user, str(user.id), str(user))


@bot.tree.command(name="remove_moderator", description="Снять права модератора")
@app_commands.describe(user="Пользователь для снятия прав")
async def remove_moderator(interaction: discord.Interaction, user: discord.User):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ Только администраторы могут использовать эту команду!", ephemeral=True)
        return
    
    data = load_data()
    if user.id not in data["moderators"]:
        await interaction.response.send_message(f"❌ {user.mention} не является модератором!", ephemeral=True)
        return
    
    data["moderators"].remove(user.id)
    save_data(data)
    
    await interaction.response.send_message(f"✅ {user.mention} больше не модератор!", ephemeral=True)
    add_log("moderator_removed", interaction.user, str(user.id), str(user))


# ============== КОМАНДЫ ВЛАДЕЛЬЦА ==============
@bot.tree.command(name="view_logs", description="Просмотр логов действий")
@app_commands.describe(limit="Количество записей для просмотра (по умолчанию 20)")
async def view_logs(interaction: discord.Interaction, limit: Optional[int] = 20):
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("❌ Только владельцы могут использовать эту команду!", ephemeral=True)
        return
    
    data = load_data()
    logs = data.get("logs", [])[-limit:]
    
    if not logs:
        await interaction.response.send_message("📋 Логи пусты.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="📋 Логи действий",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    log_text = ""
    for log in reversed(logs):
        timestamp = log.get("timestamp", "N/A")[:10]
        action = log.get("action", "N/A")
        user_name = log.get("user_name", "N/A")
        details = log.get("details", "")
        log_text += f"`{timestamp}` **{action}** - {user_name}\n"
        if details:
            log_text += f"  └ {details}\n"
    
    if len(log_text) > 4000:
        log_text = log_text[:4000] + "..."
    
    embed.description = log_text
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="add_admin", description="Выдать права администратора")
@app_commands.describe(user="Пользователь для выдачи прав")
async def add_admin(interaction: discord.Interaction, user: discord.User):
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("❌ Только владельцы могут использовать эту команду!", ephemeral=True)
        return
    
    data = load_data()
    if user.id in data["admins"]:
        await interaction.response.send_message(f"❌ {user.mention} уже является администратором!", ephemeral=True)
        return
    
    data["admins"].append(user.id)
    save_data(data)
    
    await interaction.response.send_message(f"✅ {user.mention} теперь администратор!", ephemeral=True)
    add_log("admin_added", interaction.user, str(user.id), str(user))


@bot.tree.command(name="remove_admin", description="Снять права администратора")
@app_commands.describe(user="Пользователь для снятия прав")
async def remove_admin(interaction: discord.Interaction, user: discord.User):
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("❌ Только владельцы могут использовать эту команду!", ephemeral=True)
        return
    
    data = load_data()
    if user.id not in data["admins"]:
        await interaction.response.send_message(f"❌ {user.mention} не является администратором!", ephemeral=True)
        return
    
    data["admins"].remove(user.id)
    save_data(data)
    
    await interaction.response.send_message(f"✅ {user.mention} больше не администратор!", ephemeral=True)
    add_log("admin_removed", interaction.user, str(user.id), str(user))


# ============== КОМАНДЫ РАЗРАБОТЧИКА ==============
@bot.tree.command(name="add_owner", description="Выдать права владельца")
@app_commands.describe(user="Пользователь для выдачи прав")
async def add_owner(interaction: discord.Interaction, user: discord.User):
    if not is_developer(interaction.user.id):
        await interaction.response.send_message("❌ Только разработчики могут использовать эту команду!", ephemeral=True)
        return
    
    data = load_data()
    if user.id in data["owners"]:
        await interaction.response.send_message(f"❌ {user.mention} уже является владельцем!", ephemeral=True)
        return
    
    data["owners"].append(user.id)
    save_data(data)
    
    await interaction.response.send_message(f"✅ {user.mention} теперь владелец!", ephemeral=True)
    add_log("owner_added", interaction.user, str(user.id), str(user))


@bot.tree.command(name="remove_owner", description="Снять права владельца")
@app_commands.describe(user="Пользователь для снятия прав")
async def remove_owner(interaction: discord.Interaction, user: discord.User):
    if not is_developer(interaction.user.id):
        await interaction.response.send_message("❌ Только разработчики могут использовать эту команду!", ephemeral=True)
        return
    
    data = load_data()
    if user.id not in data["owners"]:
        await interaction.response.send_message(f"❌ {user.mention} не является владельцем!", ephemeral=True)
        return
    
    data["owners"].remove(user.id)
    save_data(data)
    
    await interaction.response.send_message(f"✅ {user.mention} больше не владелец!", ephemeral=True)
    add_log("owner_removed", interaction.user, str(user.id), str(user))


@bot.tree.command(name="sync", description="Синхронизировать команды бота")
async def sync_commands(interaction: discord.Interaction):
    if not is_developer(interaction.user.id):
        await interaction.response.send_message("❌ Только разработчики могут использовать эту команду!", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    for guild in bot.guilds:
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
    await interaction.followup.send(f"✅ Команды синхронизированы для {len(bot.guilds)} серверов!", ephemeral=True)


@bot.tree.command(name="bot_stats", description="Статистика бота")
async def bot_stats(interaction: discord.Interaction):
    if not is_developer(interaction.user.id):
        await interaction.response.send_message("❌ Только разработчики могут использовать эту команду!", ephemeral=True)
        return
    
    data = load_data()
    embed = discord.Embed(
        title="📊 Статистика бота",
        color=discord.Color.gold(),
        timestamp=datetime.now()
    )
    embed.add_field(name="🏠 Серверов", value=len(bot.guilds), inline=True)
    embed.add_field(name="👥 Пользователей", value=sum(g.member_count for g in bot.guilds), inline=True)
    embed.add_field(name="📋 Зарегистрировано", value=len(data.get("registered_users", {})), inline=True)
    embed.add_field(name="👮 Модераторов", value=len(data.get("moderators", [])), inline=True)
    embed.add_field(name="🛡️ Администраторов", value=len(data.get("admins", [])), inline=True)
    embed.add_field(name="👑 Владельцев", value=len(data.get("owners", [])), inline=True)
    embed.add_field(name="📜 Записей в логах", value=len(data.get("logs", [])), inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="list_staff", description="Список всего персонала")
async def list_staff(interaction: discord.Interaction):
    if not is_moderator(interaction.user.id):
        await interaction.response.send_message("❌ У вас нет прав для этого действия!", ephemeral=True)
        return
    
    data = load_data()
    embed = discord.Embed(
        title="👥 Список персонала",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    devs = [f"<@{uid}>" for uid in DEVELOPER_IDS]
    embed.add_field(name="🔧 Разработчики", value="\n".join(devs) if devs else "Нет", inline=False)
    
    owners = [f"<@{uid}>" for uid in data.get("owners", [])]
    embed.add_field(name="👑 Владельцы", value="\n".join(owners) if owners else "Нет", inline=False)
    
    admins = [f"<@{uid}>" for uid in data.get("admins", [])]
    embed.add_field(name="🛡️ Администраторы", value="\n".join(admins) if admins else "Нет", inline=False)
    
    mods = [f"<@{uid}>" for uid in data.get("moderators", [])]
    embed.add_field(name="👮 Модераторы", value="\n".join(mods) if mods else "Нет", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="registered_list", description="Список зарегистрированных персонажей")
async def registered_list(interaction: discord.Interaction):
    if not is_moderator(interaction.user.id):
        await interaction.response.send_message("❌ У вас нет прав для этого действия!", ephemeral=True)
        return
    
    data = load_data()
    registered = data.get("registered_users", {})
    
    if not registered:
        await interaction.response.send_message("📋 Нет зарегистрированных персонажей.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="📋 Зарегистрированные персонажи",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    
    description = ""
    for user_id, info in list(registered.items())[:25]:
        description += f"<@{user_id}> - **{info['nickname']}**\n└ Steam ID: `{info['steam_id']}`\n\n"
    
    if len(registered) > 25:
        description += f"... и ещё {len(registered) - 25} персонажей"
    
    embed.description = description
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ============== СОБЫТИЯ ==============
@bot.event
async def on_ready():
    print(f"✅ Бот {bot.user} запущен!")
    print(f"📊 Серверов: {len(bot.guilds)}")
    print(f"🌐 Веб-панель: http://localhost:{WEB_PORT}")
    print(f"🔗 Ссылка для приглашения:")
    print(f"https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot%20applications.commands")
    
    activity = discord.Streaming(
        name=BOT_ACTIVITY_TEXT,
        url=SERVER_INVITE
    )
    await bot.change_presence(activity=activity, status=discord.Status.online)
    print(f"🎮 Статус установлен: {BOT_ACTIVITY_TEXT}")
    
    # Синхронизация команд для каждого сервера (мгновенная)
    try:
        for guild in bot.guilds:
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f"✅ Синхронизировано {len(synced)} команд для сервера: {guild.name}")
    except Exception as e:
        print(f"❌ Ошибка синхронизации: {e}")
    
    # Очистка глобальных команд (убираем дубли)
    try:
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        print("🧹 Глобальные дубли очищены")
    except Exception as e:
        print(f"⚠️ Ошибка очистки глобальных команд: {e}")


@bot.event
async def on_guild_join(guild):
    print(f"➕ Бот добавлен на сервер: {guild.name}")
    add_log("guild_join", bot.user, str(guild.id), guild.name)


@bot.event
async def on_guild_remove(guild):
    print(f"➖ Бот удалён с сервера: {guild.name}")


# ============== ЗАПУСК ==============
def run_bot():
    bot.run(TOKEN)

# Запуск бота в отдельном потоке при любом способе импорта
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()
print(f"🤖 Discord бот запущен в отдельном потоке")

if __name__ == "__main__":
    # Прямой запуск — веб-сервер в основном потоке
    print(f"🌐 Веб-сервер запущен на порту {WEB_PORT}")
    run_web()
