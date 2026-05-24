# =========================
# FULL UPGRADED VAULTRIX BOT
# COMPONENTS V2
# NO EMBEDS
# =========================

import os
import json
import random
import asyncio
import time
from pathlib import Path

import discord
from discord.ext import commands
from discord import ui
from dotenv import load_dotenv

# =========================
# LOAD ENV
# =========================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

TOKEN = os.getenv("TOKEN")
PREFIX = "v!"

if not TOKEN:
    raise ValueError("TOKEN missing in .env")

# =========================
# CONFIG
# =========================

DB_FILE = "database.json"
PREFIX_FILE = "prefixes.json"
NO_PREFIX_FILE = "noprefix.json"
CHANNELS_FILE = "channels.json"

START_BALANCE = 1000
DAILY_REWARD = 1000
MAX_BET = 250000
LOAN_LIMIT = 100000
LOAN_INTEREST_RATE = 0.10
LOAN_OVERDUE_PENALTY = 0.10
LOAN_DUE_SECONDS = 2 * 24 * 60 * 60

OWNER_IDS = [
    1396844211038458018
]
def load_channels():

    if not os.path.exists(CHANNELS_FILE):

        with open(CHANNELS_FILE, "w") as f:
            json.dump({}, f)

    with open(CHANNELS_FILE, "r") as f:
        return json.load(f)


def save_channels(data):

    with open(CHANNELS_FILE, "w") as f:
        json.dump(data, f, indent=4)

# =========================
# BOT
# =========================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

def load_prefixes():

    if not os.path.exists(PREFIX_FILE):

        with open(PREFIX_FILE, "w") as f:
            json.dump({}, f)

    with open(PREFIX_FILE, "r") as f:
        return json.load(f)


def load_no_prefix_users():

    if not os.path.exists(NO_PREFIX_FILE):

        with open(NO_PREFIX_FILE, "w") as f:
            json.dump([], f)

    with open(NO_PREFIX_FILE, "r") as f:
        return json.load(f)


def save_no_prefix_users(users):

    with open(NO_PREFIX_FILE, "w") as f:
        json.dump(users, f, indent=4)


def get_prefix(bot, message):

    prefixes = load_prefixes()
    no_prefix_users = load_no_prefix_users()

    guild_id = str(message.guild.id) if message.guild else "dm"
    server_prefix = prefixes.get(guild_id, PREFIX)

    prefix_list = [
        server_prefix,
        server_prefix.lower(),
        server_prefix.upper(),
        server_prefix.capitalize()
    ]

    if message.author and message.author.id in no_prefix_users:
        return commands.when_mentioned_or(*prefix_list, "")(bot, message)

    return commands.when_mentioned_or(*prefix_list)(bot, message)


bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents,
    help_command=None,
    case_insensitive=True
)

# =========================
# DATABASE
# =========================

DEFAULT_USER = {
    "wallet": START_BALANCE,
    "bank": 0,
    "wins": 0,
    "losses": 0,
    "profit": 0,
    "streak": 0,
    "xp": 0,
    "level": 1,
    "rank": "Bronze",
    "title": "Rookie Gambler",
    "badges": [],
    "pets": [],
    "inventory": [],
    "history": []
}


def load_db():

    if not os.path.exists(DB_FILE):

        with open(DB_FILE, "w") as f:
            json.dump({}, f)

    with open(DB_FILE, "r") as f:
        return json.load(f)


def save_db(data):

    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)


def get_user(uid):
    data = load_db()
    uid = str(uid)

    if uid not in data:
        data[uid] = {
            key: value.copy() if isinstance(value, list) else value
            for key, value in DEFAULT_USER.items()
        }
    else:
        for key, value in DEFAULT_USER.items():
            if key not in data[uid]:
                data[uid][key] = value.copy() if isinstance(value, list) else value

    save_db(data)
    return data[uid]


def update_user(uid, user_data):

    data = load_db()

    data[str(uid)] = user_data

    save_db(data)


def add_history(uid, text):

    user = get_user(uid)

    user["history"].insert(
        0,
        f"{time.strftime('%H:%M')} • {text}"
    )

    user["history"] = user["history"][:10]

    update_user(uid, user)


def add_xp(uid, amount):

    user = get_user(uid)

    user["xp"] += amount

    needed = user["level"] * 500

    while user["xp"] >= needed:

        user["xp"] -= needed
        user["level"] += 1

        needed = user["level"] * 500

    update_user(uid, user)


def update_rank(user):

    total = user["wallet"] + user["bank"]

    if total >= 1000000:
        user["rank"] = "Void"

    elif total >= 100000:
        user["rank"] = "Crimson"

    elif total >= 50000:
        user["rank"] = "Diamond"

    elif total >= 10000:
        user["rank"] = "Gold"

    elif total >= 5000:
        user["rank"] = "Silver"

    else:
        user["rank"] = "Bronze"


def win(uid, amount):

    user = get_user(uid)

    user["wallet"] += amount
    user["wins"] += 1
    user["profit"] += amount
    user["streak"] += 1

    add_xp(uid, 25)

    update_rank(user)

    update_user(uid, user)

    add_history(uid, f"Won {amount}")

    return user["wallet"]


def lose(uid, amount):

    user = get_user(uid)

    user["wallet"] -= amount
    user["losses"] += 1
    user["profit"] -= amount
    user["streak"] = 0

    add_xp(uid, 10)

    update_rank(user)

    update_user(uid, user)

    add_history(uid, f"Lost {amount}")

    return user["wallet"]

# =========================
# UI
# =========================

def create_view(title, sections=None):

    sections = sections or []

    view = ui.LayoutView()

    items = [
        ui.TextDisplay(
            f"## {title}"
        ),

        ui.Separator(
            spacing=discord.SeparatorSpacing.large,
            visible=True
        )
    ]

    for section in sections:

        # skip empty text because Discord Components V2 crashes on ""
        if section is None or str(section).strip() == "":
            continue

        items.append(
            ui.TextDisplay(str(section))
        )

        items.append(
            ui.Separator(
                spacing=discord.SeparatorSpacing.large,
                visible=True
            )
        )

    items.append(
        ui.TextDisplay(
            "-# Vaultrix Casino • made by odxbrosky"
        )
    )

    container = ui.Container(*items)

    view.add_item(container)

    return view

async def check_channel(ctx):

    if ctx.author.id in OWNER_IDS:
        return True

    data = load_channels()

    guild_id = str(ctx.guild.id)

    if guild_id not in data:
        return True

    allowed_channel = data[guild_id]

    if ctx.channel.id != allowed_channel:

        await ctx.send(
            view=create_view(
                "🚫 Wrong Channel",
                [
                    f"Use bot commands in <#{allowed_channel}> only."
                ]
            ),
            delete_after=5
        )

        return False

    return True
# =========================
# HELP VIEW
# =========================
def current_prefix_for_guild(guild):
    prefixes = load_prefixes()

    if guild:
        return prefixes.get(str(guild.id), PREFIX)

    return PREFIX
class HelpView(ui.LayoutView):

    def __init__(self, user, guild):
        super().__init__(timeout=120)

        self.user = user
        self.guild = guild
        self.prefix = current_prefix_for_guild(guild)

        economy = ui.Button(
            label="Economy",
            emoji="💰",
            style=discord.ButtonStyle.secondary
        )

        casino = ui.Button(
            label="Casino",
            emoji="🎰",
            style=discord.ButtonStyle.danger
        )

        profile = ui.Button(
            label="Profile",
            emoji="👤",
            style=discord.ButtonStyle.secondary
        )

        settings = ui.Button(
            label="Settings",
            emoji="⚙️",
            style=discord.ButtonStyle.secondary
        )

        economy.callback = self.economy_tab
        casino.callback = self.casino_tab
        profile.callback = self.profile_tab
        settings.callback = self.settings_tab

        self.row = ui.ActionRow(
            economy,
            casino,
            profile,
            settings
        )

        self.build_home()

    async def interaction_check(self, interaction):

        if interaction.user.id != self.user.id:

            await interaction.response.send_message(
                "This help menu is not yours.",
                ephemeral=True
            )

            return False

        return True

    def build(self, title, sections):

        self.clear_items()

        items = [
            ui.TextDisplay(
                f"## {title}\n"
                f"Requested by {self.user.mention}\n"
                f"Current Prefix: `{self.prefix}`"
            ),

            ui.Separator(
                spacing=discord.SeparatorSpacing.large,
                visible=True
            )
        ]

        for section in sections:

            items.append(ui.TextDisplay(section))

            items.append(
                ui.Separator(
                    spacing=discord.SeparatorSpacing.large,
                    visible=True
                )
            )

        items.append(self.row)

        items.append(
            ui.TextDisplay(
                "-# Vaultrix Help • Components V2 • No embeds"
            )
        )

        self.add_item(
            ui.Container(*items)
        )

    def build_home(self):

        p = self.prefix

        self.build(
            "📚 Vaultrix Help",
            [
                f"Welcome to Vaultrix Casino.\nUse buttons below to browse commands.",
                f"Example: `{p}balance`, `{p}slots 100`, `{p}setprefix !`"
            ]
        )

    async def economy_tab(self, interaction):

        p = self.prefix

        self.build(
            "💰 Economy Commands",
            [
                f"`{p}balance` — check balance\n"
                f"`{p}daily` — claim daily coins\n"
                f"`{p}work` — earn coins\n"
                f"`{p}deposit <amount>` — deposit coins\n"
                f"`{p}withdraw <amount>` — withdraw coins\n"
                f"`{p}give @user <amount>` — give coins\n"
                f"`{p}deposit <amount>` — deposit wallet coins\n"
                f"`{p}withdraw <amount>` — withdraw coins from bank\n"
                f"`{p}loan <amount>` — take a loan\n"
                f"`{p}repay <amount>` — repay loan\n"
                f"`{p}debt` — check debt\n"
                f"`{p}paytax` — pay tax\n"
                f"`{p}interest` — claim hourly bank interest\n"
            ]
        )

        await interaction.response.edit_message(view=self)

    async def casino_tab(self, interaction):

        p = self.prefix

        self.build(
            "🎰 Casino Commands",
            [
                f"`{p}coinflip <amount>` — coinflip\n"
                f"`{p}dice <amount>` — dice roll\n"
                f"`{p}slots <amount>` — slots\n"
                f"`{p}roulette <amount> red/black` — roulette\n"
                f"`{p}blackjack <amount>` — blackjack\n"
                f"`{p}mines <amount>` — mines game\n"
                f"`{p}mines <amount>` — mines game\n"
                f"`{p}tower <amount>` — tower climb\n"
                f"`{p}crash <amount> <cashout>` — crash game\n"
                f"`{p}case` — open a case\n"
                f"`{p}coinrain <amount>` — start coin rain\n"
            ]
        )

        await interaction.response.edit_message(view=self)

    async def profile_tab(self, interaction):

        p = self.prefix

        self.build(
            "👤 Profile Commands",
            [
                f"`{p}profile` — profile card\n"
                f"`{p}leaderboard` — richest users\n"
                f"`{p}history` — transaction history\n"
                f"`{p}stats` — player stats\n"
                f"`{p}shop` — shop menu\n"
                f"`{p}petshop` — pet shop"
            ]
        )

        await interaction.response.edit_message(view=self)

    async def settings_tab(self, interaction):

        p = self.prefix

        self.build(
            "⚙️ Settings Commands",
            [
                f"`{p}setprefix <prefix>` — change server prefix\n"
                f"`{p}resetprefix` — reset prefix to `{PREFIX}`\n\n"
                f"Example:\n"
                f"`{p}setprefix !`\n"
                f"Then use `!help`"
            ]
        )

        await interaction.response.edit_message(view=self)
@bot.hybrid_command(name="setprefix")
@commands.has_permissions(administrator=True)
async def setprefix(ctx, prefix: str):

    if len(prefix) > 5:

        return await ctx.send(
            view=create_view(
                "❌ Invalid Prefix",
                [
                    "Prefix must be under 5 characters."
                ]
            )
        )

    prefixes = load_prefixes()

    prefixes[str(ctx.guild.id)] = prefix

    with open(PREFIX_FILE, "w") as f:
        json.dump(prefixes, f, indent=4)

    await ctx.send(
        view=create_view(
            "⚙️ Prefix Updated",
            [
                f"New Prefix: `{prefix}`"
            ]
        )
    )
@bot.hybrid_command(name="resetprefix")
@commands.has_permissions(administrator=True)
async def resetprefix(ctx):

    prefixes = load_prefixes()

    prefixes[str(ctx.guild.id)] = PREFIX

    with open(PREFIX_FILE, "w") as f:
        json.dump(prefixes, f, indent=4)

    await ctx.send(
        view=create_view(
            "♻️ Prefix Reset",
            [
                f"Prefix reset to `{PREFIX}`"
            ]
        )
    )
# =========================
# EVENTS
# =========================

@bot.event
async def on_ready():

    print(f"✅ Logged in as {bot.user}")

    statuses = [

        ("watching", "v!help • Vaultrix Casino"),
        ("playing", "Mines with gamblers"),
        ("watching", "500+ casino players"),
        ("listening", "Coin flips"),
        ("competing", "Jackpot battles"),
        ("playing", "Crash & Roulette"),
        ("watching", "Made by odxbrosky")

    ]

    while True:

        for activity_type, text in statuses:

            if activity_type == "playing":

                activity = discord.Game(
                    name=text
                )

            elif activity_type == "watching":

                activity = discord.Activity(
                    type=discord.ActivityType.watching,
                    name=text
                )

            elif activity_type == "listening":

                activity = discord.Activity(
                    type=discord.ActivityType.listening,
                    name=text
                )

            elif activity_type == "competing":

                activity = discord.Activity(
                    type=discord.ActivityType.competing,
                    name=text
                )

            else:

                activity = discord.Game(
                    name=text
                )

            await bot.change_presence(
                status=discord.Status.online,
                activity=activity
            )

            await asyncio.sleep(5)

# =========================
# HELP
# =========================

@bot.hybrid_command(name="help")
async def help_cmd(ctx):
    if not await check_channel(ctx):
        return

    await ctx.send(
        view=HelpView(
            ctx.author,
            ctx.guild
        )
    )

# =========================
# BALANCE
# =========================

@bot.hybrid_command(name="balance", aliases=["bal"])
async def balance(ctx):
    if not await check_channel(ctx):
        return

    user = get_user(ctx.author.id)

    await ctx.send(
        view=create_view(
            "💰 Balance",
            [
                f"🪙 Wallet: `{user['wallet']}`",
                f"🏦 Bank: `{user['bank']}`",
                f"👑 Rank: `{user['rank']}`"
            ]
        )
    )

# =========================
# DAILY
# =========================

@bot.hybrid_command(name="daily")
async def daily(ctx):

    amount = random.randint(100, 1000)

    user = get_user(ctx.author.id)

    user["wallet"] += amount

    update_user(ctx.author.id, user)

    await ctx.send(
        view=create_view(
            "🎁 Daily Reward",
            [
                f"You received 🪙 `{amount}` coins."
            ]
        )
    )

# =========================
# WORK
# =========================

@bot.hybrid_command(name="work")
async def work(ctx):

    jobs = [
        "Vault Guard",
        "Crypto Miner",
        "Dealer",
        "Hacker"
    ]

    job = random.choice(jobs)

    pay = random.randint(200, 1500)

    user = get_user(ctx.author.id)

    user["wallet"] += pay

    update_user(ctx.author.id, user)

    await ctx.send(
        view=create_view(
            "💼 Work Complete",
            [
                f"Job: **{job}**",
                f"Earned: 🪙 `{pay}`"
            ]
        )
    )
@bot.hybrid_command(name="deposit", aliases=["dep"])
async def deposit(ctx, amount: int):
    user = get_user(ctx.author.id)

    if amount <= 0:
        return await ctx.send(
            view=create_view("❌ Invalid Amount", ["Amount must be above `0`."])
        )

    if user["wallet"] < amount:
        return await ctx.send(
            view=create_view("❌ Not Enough Coins", ["You don't have enough coins in wallet."])
        )

    user["wallet"] -= amount
    user["bank"] += amount

    update_user(ctx.author.id, user)
    add_history(ctx.author.id, f"Deposited {amount} coins")

    await ctx.send(
        view=create_view(
            "🏦 Deposit Successful",
            [
                f"Deposited 🪙 `{amount}` coins.",
                f"Wallet: 🪙 `{user['wallet']}`",
                f"Bank: 🏦 `{user['bank']}`"
            ]
        )
    )


@bot.hybrid_command(name="withdraw", aliases=["with"])
async def withdraw(ctx, amount: int):
    user = get_user(ctx.author.id)

    if amount <= 0:
        return await ctx.send(
            view=create_view("❌ Invalid Amount", ["Amount must be above `0`."])
        )

    if user["bank"] < amount:
        return await ctx.send(
            view=create_view("❌ Not Enough Coins", ["You don't have enough coins in bank."])
        )

    user["bank"] -= amount
    user["wallet"] += amount

    update_user(ctx.author.id, user)
    add_history(ctx.author.id, f"Withdrew {amount} coins")

    await ctx.send(
        view=create_view(
            "🏦 Withdraw Successful",
            [
                f"Withdrawn 🪙 `{amount}` coins.",
                f"Wallet: 🪙 `{user['wallet']}`",
                f"Bank: 🏦 `{user['bank']}`"
            ]
        )
    )
# =========================
# COINFLIP
# =========================

@bot.hybrid_command(name="coinflip", aliases=["cf"])
async def coinflip(
    ctx,
    amount: int,
    side: str = "h"
):
    if not await check_channel(ctx):
        return
    if await block_if_loan_overdue(ctx):
        return

    side = side.lower()

    if side in ["h", "head", "heads"]:
        side = "heads"

    elif side in ["t", "tail", "tails"]:
        side = "tails"

    else:

        return await ctx.send(
            view=create_view(
                "❌ Invalid Side",
                [
                    "Choose `h` or `t`.",
                    "Example: `v!cf 1000 h`"
                ]
            )
        )

    user = get_user(ctx.author.id)

    if amount <= 0:

        return await ctx.send(
            view=create_view(
                "❌ Invalid Bet",
                [
                    "Bet amount must be above `0`."
                ]
            )
        )

    if amount > MAX_BET:

        return await ctx.send(
            view=create_view(
                "❌ Max Bet Reached",
                [
                    f"Max bet is 🪙 `{MAX_BET}`."
                ]
            )
        )

    if user["wallet"] < amount:

        return await ctx.send(
            view=create_view(
                "❌ Not Enough Coins",
                [
                    "You don't have enough wallet coins."
                ]
            )
        )

    # =========================
    # LOADING ANIMATION
    # =========================

    loading = await ctx.send(
        view=create_view(
            "🪙 Coinflip",
            [
                f"🎯 Choice: **{side.upper()}**",
                "🪙 Flipping Coin..."
            ]
        )
    )

    animations = [
        "🪙 Flipping Coin.",
        "🪙 Flipping Coin..",
        "🪙 Flipping Coin..."
    ]

    for i in range(6):

        await loading.edit(
            view=create_view(
                "🪙 Coinflip",
                [
                    f"🎯 Choice: **{side.upper()}**",
                    animations[i % len(animations)]
                ]
            )
        )

        await asyncio.sleep(0.35)

    # =========================
    # FINAL RESULT
    # =========================

    result = random.choice([
        "heads",
        "tails"
    ])

    won = side == result

    if won:

        user["wallet"] += amount
        user["wins"] += 1
        user["streak"] += 1
        user["profit"] += amount

        text = "✅ You won!"

        add_history(
            ctx.author.id,
            f"Won {amount} in coinflip"
        )

    else:

        user["wallet"] -= amount
        user["losses"] += 1
        user["streak"] = 0
        user["profit"] -= amount

        text = "❌ You lost!"

        add_history(
            ctx.author.id,
            f"Lost {amount} in coinflip"
        )

    add_xp(ctx.author.id, 20)

    update_rank(user)

    update_user(ctx.author.id, user)

    await loading.edit(
        view=create_view(
            "🪙 Coinflip Result",
            [
                f"🎯 Your Choice: **{side.upper()}**",
                f"🪙 Coin Landed: **{result.upper()}**",
                text,
                f"Balance: 🪙 `{user['wallet']}`"
            ]
        )
    )

# =========================
# SLOTS
# =========================

@bot.hybrid_command(name="slots", aliases=["s"])
async def slots(ctx, amount: int):
    if not await check_channel(ctx):
        return
    if await block_if_loan_overdue(ctx):
        return
    user = get_user(ctx.author.id)
    
    if amount <= 0:
        return await ctx.send(
            view=neon_view("❌ Invalid Bet", ctx.author.id, ["Bet must be above `0`."])
        )

    if amount > MAX_BET:
        return await ctx.send(
            view=neon_view("❌ Max Bet", ctx.author.id, [f"Max bet is 🪙 `{MAX_BET}`."])
        )

    if user["wallet"] < amount:
        return await ctx.send(
            view=neon_view("❌ Not Enough Coins", ctx.author.id, ["You don't have enough coins."])
        )

    icons = ["🍒", "🍋", "🔔", "💎", "7️⃣"]
    msg = await ctx.send(
        view=neon_view(
            "🎰 Slots Booting",
            ctx.author.id,
            [
                "`❔ | ❔ | ❔`",
                "`Loading machine...`"
            ]
        )
    )

    final = None

    for i in range(1, 8):
        spin = [random.choice(icons) for _ in range(3)]
        final = spin
        bar = progress_bar(i, 7)

        await msg.edit(
            view=neon_view(
                "🎰 Slots Spinning",
                ctx.author.id,
                [
                    f"`{' | '.join(spin)}`",
                    f"`{bar}` `{i}/7`"
                ]
            )
        )
        await asyncio.sleep(0.35)

    won = final[0] == final[1] == final[2]

    if won:
        reward = amount * 3
        user["wallet"] += reward
        user["wins"] += 1
        user["profit"] += reward
        result = f"💎 **JACKPOT!** You won 🪙 `{reward}`."
    else:
        user["wallet"] -= amount
        user["losses"] += 1
        user["profit"] -= amount
        result = f"❌ No match. You lost 🪙 `{amount}`."

    update_user(ctx.author.id, user)

    await msg.edit(
        view=neon_view(
            "🎰 Slots Result",
            ctx.author.id,
            [
                f"`{' | '.join(final)}`",
                result,
                f"Balance: 🪙 `{user['wallet']}`"
            ]
        )
    )
class CasinoPages(ui.LayoutView):
    def __init__(self, user):
        super().__init__(timeout=120)
        self.user = user
        self.page = 0

        self.prev_btn = ui.Button(label="Back", emoji="⬅️", style=discord.ButtonStyle.secondary)
        self.next_btn = ui.Button(label="Next", emoji="➡️", style=discord.ButtonStyle.secondary)

        self.prev_btn.callback = self.prev_page
        self.next_btn.callback = self.next_page

        self.pages = [
            {
                "title": "🎰 Casino Games",
                "body": "`v!cf 100 h` — Coinflip\n`v!slots 100` — Slots\n`v!dice 100` — Dice"
            },
            {
                "title": "💣 Risk Games",
                "body": "`v!mines 100` — Mines\n`v!tower 100` — Tower\n`v!crash 100 2.0` — Crash"
            },
            {
                "title": "🎁 Events",
                "body": "`v!case` — Case Opening\n`v!claimrain` — Claim Coin Rain"
            }
        ]

        self.build()

    async def interaction_check(self, interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This menu is not yours.", ephemeral=True)
            return False
        return True

    def build(self):
        self.clear_items()

        page = self.pages[self.page]
        theme = get_theme(self.user.id)

        self.add_item(
            ui.Container(
                ui.TextDisplay(
                    f"## {theme['emoji']} {page['title']}\n"
                    f"Page `{self.page + 1}/{len(self.pages)}`"
                ),
                ui.Separator(spacing=discord.SeparatorSpacing.large, visible=True),
                ui.TextDisplay(page["body"]),
                ui.Separator(spacing=discord.SeparatorSpacing.large, visible=True),
                ui.ActionRow(self.prev_btn, self.next_btn),
                ui.TextDisplay(f"-# {theme['footer']}")
            )
        )

    async def prev_page(self, interaction):
        self.page = (self.page - 1) % len(self.pages)
        self.build()
        await interaction.response.edit_message(view=self)

    async def next_page(self, interaction):
        self.page = (self.page + 1) % len(self.pages)
        self.build()
        await interaction.response.edit_message(view=self)


@bot.hybrid_command(name="pages")
async def pages(ctx):
    await ctx.send(view=CasinoPages(ctx.author))
class ProfileTabs(ui.LayoutView):
    def __init__(self, user):
        super().__init__(timeout=120)
        self.user = user

        overview = ui.Button(label="Overview", emoji="👤", style=discord.ButtonStyle.secondary)
        stats = ui.Button(label="Stats", emoji="📊", style=discord.ButtonStyle.secondary)
        inventory = ui.Button(label="Inventory", emoji="🎒", style=discord.ButtonStyle.secondary)

        overview.callback = self.overview
        stats.callback = self.stats
        inventory.callback = self.inventory

        self.row = ui.ActionRow(overview, stats, inventory)
        self.build_overview()

    async def interaction_check(self, interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This profile is not yours.", ephemeral=True)
            return False
        return True

    def build_base(self, title, body):
        self.clear_items()
        theme = get_theme(self.user.id)

        self.add_item(
            ui.Container(
                ui.TextDisplay(f"## {theme['emoji']} {title}\n{self.user.mention}"),
                ui.Separator(spacing=discord.SeparatorSpacing.large, visible=True),
                ui.TextDisplay(body),
                ui.Separator(spacing=discord.SeparatorSpacing.large, visible=True),
                self.row,
                ui.TextDisplay(f"-# {theme['footer']}")
            )
        )

    def build_overview(self):
        user = get_user(self.user.id)
        self.build_base(
            "Profile Overview",
            f"Rank: `{user['rank']}`\nLevel: `{user['level']}`\nWallet: 🪙 `{user['wallet']}`\nBank: 🏦 `{user['bank']}`"
        )

    async def overview(self, interaction):
        self.build_overview()
        await interaction.response.edit_message(view=self)

    async def stats(self, interaction):
        user = get_user(self.user.id)
        self.build_base(
            "Profile Stats",
            f"Wins: `{user['wins']}`\nLosses: `{user['losses']}`\nProfit: `{user['profit']}`\nStreak: `{user['streak']}`"
        )
        await interaction.response.edit_message(view=self)

    async def inventory(self, interaction):
        user = get_user(self.user.id)
        inv = user.get("inventory", [])
        badges = user.get("badges", [])
        pets = user.get("pets", [])

        self.build_base(
            "Inventory",
            f"Items: `{', '.join(inv) if inv else 'None'}`\nBadges: `{', '.join(badges) if badges else 'None'}`\nPets: `{', '.join(pets) if pets else 'None'}`"
        )
        await interaction.response.edit_message(view=self)


@bot.hybrid_command(name="profiletabs")
async def profiletabs(ctx):
    await ctx.send(view=ProfileTabs(ctx.author))
@bot.hybrid_command(name="theme")
async def theme(ctx, theme_name: str = None):
    user = get_user(ctx.author.id)

    if theme_name is None:
        available = "\n".join([f"`{name}` — {data['name']}" for name, data in THEMES.items()])
        return await ctx.send(
            view=neon_view(
                "🎨 Casino Themes",
                ctx.author.id,
                [
                    available,
                    "Use `v!theme crimson`, `v!theme cyan`, or `v!theme gold`."
                ]
            )
        )

    theme_name = theme_name.lower()

    if theme_name not in THEMES:
        return await ctx.send(
            view=neon_view(
                "❌ Theme Not Found",
                ctx.author.id,
                ["Use `v!theme` to see available themes."]
            )
        )

    user["theme"] = theme_name
    update_user(ctx.author.id, user)

    await ctx.send(
        view=neon_view(
            "🎨 Theme Updated",
            ctx.author.id,
            [f"Your casino theme is now **{THEMES[theme_name]['name']}**."]
        )
    )

# =========================
# PROFILE
# =========================

@bot.hybrid_command(name="profile")
async def profile(ctx):

    user = get_user(ctx.author.id)

    await ctx.send(
        view=create_view(
            "👤 Profile",
            [
                f"👑 Rank: `{user['rank']}`",
                f"⭐ Level: `{user['level']}`",
                f"🔥 Streak: `{user['streak']}`"
            ]
        )
    )

# =========================
# LEADERBOARD
# =========================

@bot.hybrid_command(name="leaderboard")
async def leaderboard(ctx):

    data = load_db()

    sorted_users = sorted(
        data.items(),
        key=lambda x: x[1]["wallet"],
        reverse=True
    )[:10]

    text = ""

    for i, (uid, info) in enumerate(
        sorted_users,
        start=1
    ):

        text += (
            f"**#{i}** <@{uid}> — "
            f"🪙 `{info['wallet']}`\n"
        )

    await ctx.send(
        view=create_view(
            "🏆 Leaderboard",
            [text]
        )
    )

# =========================
# HISTORY
# =========================

@bot.hybrid_command(name="history")
async def history(ctx):

    user = get_user(ctx.author.id)

    hist = (
        "\n".join(user["history"])
        if user["history"]
        else "No history."
    )

    await ctx.send(
        view=create_view(
            "🧾 History",
            [hist]
        )
    )

# =========================
# OWNER COMMANDS
# =========================

def is_owner(uid):

    return uid in OWNER_IDS


@bot.hybrid_command(name="giftcoins")
async def giftcoins(
    ctx,
    member: discord.Member,
    amount: int
):

    if not is_owner(ctx.author.id):

        return await ctx.send(
            view=create_view(
                "❌ Owner Only",
                [
                    "You are not owner."
                ]
            )
        )

    user = get_user(member.id)

    user["wallet"] += amount

    update_user(member.id, user)

    await ctx.send(
        view=create_view(
            "🎁 Coins Gifted",
            [
                f"Gave 🪙 `{amount}` to {member.mention}"
            ]
        )
    )
@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if bot.user in message.mentions and message.content.strip() in [
        bot.user.mention,
        f"<@!{bot.user.id}>"
    ]:
        prefix = current_prefix_for_guild(message.guild)

        ping = round(bot.latency * 1000)

        await message.channel.send(
            view=create_view(
                "🤖 Vaultrix Bot Info",
                [
                    f"**Bot Name:** `{bot.user.name}`",
                    f"**Language:** `Python / discord.py`",
                    f"**Prefix:** `{prefix}`",
                    f"**Ping:** `{ping}ms`",
                    f"**Branding:** Made by **odxbrosky**"
                ]
            )
        )

        return

    await bot.process_commands(message)
class BlackjackView(ui.LayoutView):

    def __init__(self, player, amount):
        super().__init__(timeout=60)

        self.player = player
        self.amount = amount

        self.player_cards = [
            self.draw_card(),
            self.draw_card()
        ]

        self.dealer_cards = [
            self.draw_card(),
            self.draw_card()
        ]

        self.hit_button = ui.Button(
            label="Hit",
            emoji="➕",
            style=discord.ButtonStyle.danger
        )

        self.stand_button = ui.Button(
            label="Stand",
            emoji="🛑",
            style=discord.ButtonStyle.secondary
        )

        self.hit_button.callback = self.hit
        self.stand_button.callback = self.stand

        self.build()

    def draw_card(self):
        return random.randint(1, 11)

    def total(self, cards):
        return sum(cards)

    def build(self, result=None):
        self.clear_items()

        items = [
            ui.TextDisplay(
                f"## 🃏 Blackjack\n"
                f"Player: {self.player.mention}\n"
                f"Bet: 🪙 `{self.amount}`\n\n"
                f"Your Cards: `{self.player_cards}` = **{self.total(self.player_cards)}**\n"
                f"Dealer Shows: `{self.dealer_cards[0]}`"
            ),

            ui.Separator(
                spacing=discord.SeparatorSpacing.large,
                visible=True
            )
        ]

        if result:
            items.append(
                ui.TextDisplay(result)
            )

        else:
            items.append(
                ui.ActionRow(
                    self.hit_button,
                    self.stand_button
                )
            )

        items.append(
            ui.TextDisplay(
                "-# Vaultrix Blackjack • Made by odxbrosky"
            )
        )

        self.add_item(
            ui.Container(*items)
        )

    async def interaction_check(self, interaction):

        if interaction.user.id != self.player.id:

            await interaction.response.send_message(
                "This blackjack game is not yours.",
                ephemeral=True
            )

            return False

        return True

    async def hit(self, interaction):

        self.player_cards.append(
            self.draw_card()
        )

        if self.total(self.player_cards) > 21:

            user = get_user(self.player.id)

            user["wallet"] -= self.amount
            user["losses"] += 1
            user["streak"] = 0
            user["profit"] -= self.amount

            update_user(self.player.id, user)

            add_history(
                self.player.id,
                f"Lost {self.amount} in blackjack"
            )

            self.build(
                f"💥 **Bust! You lost** 🪙 `{self.amount}`.\n"
                f"Balance: 🪙 `{user['wallet']}`"
            )

            return await interaction.response.edit_message(
                view=self
            )

        self.build()

        await interaction.response.edit_message(
            view=self
        )

    async def stand(self, interaction):

        while self.total(self.dealer_cards) < 17:

            self.dealer_cards.append(
                self.draw_card()
            )

        player_total = self.total(self.player_cards)
        dealer_total = self.total(self.dealer_cards)

        user = get_user(self.player.id)

        if dealer_total > 21 or player_total > dealer_total:

            user["wallet"] += self.amount
            user["wins"] += 1
            user["streak"] += 1
            user["profit"] += self.amount

            result = (
                f"✅ **You won!**\n"
                f"Dealer Cards: `{self.dealer_cards}` = **{dealer_total}**\n"
                f"Reward: 🪙 `{self.amount}`"
            )

            add_history(
                self.player.id,
                f"Won {self.amount} in blackjack"
            )

        elif player_total == dealer_total:

            result = (
                f"➖ **Draw!**\n"
                f"Dealer Cards: `{self.dealer_cards}` = **{dealer_total}**\n"
                f"No coins lost."
            )

            add_history(
                self.player.id,
                "Draw in blackjack"
            )

        else:

            user["wallet"] -= self.amount
            user["losses"] += 1
            user["streak"] = 0
            user["profit"] -= self.amount

            result = (
                f"❌ **You lost!**\n"
                f"Dealer Cards: `{self.dealer_cards}` = **{dealer_total}**\n"
                f"Lost: 🪙 `{self.amount}`"
            )

            add_history(
                self.player.id,
                f"Lost {self.amount} in blackjack"
            )

        update_rank(user)
        update_user(self.player.id, user)

        self.build(
            f"{result}\n\n"
            f"Balance: 🪙 `{user['wallet']}`"
        )

        await interaction.response.edit_message(
            view=self
        )
@bot.hybrid_command(name="blackjack", aliases=["bj"])
async def blackjack(ctx, amount: int):
    if not await check_channel(ctx):
        return
    if await block_if_loan_overdue(ctx):
        return

    user = get_user(ctx.author.id)

    if amount <= 0:

        return await ctx.send(
            view=create_view(
                "❌ Invalid Bet",
                [
                    "Bet amount must be above `0`."
                ]
            )
        )

    if amount > MAX_BET:

        return await ctx.send(
            view=create_view(
                "❌ Max Bet Reached",
                [
                    f"Max bet is 🪙 `{MAX_BET}`."
                ]
            )
        )

    if user["wallet"] < amount:

        return await ctx.send(
            view=create_view(
                "❌ Not Enough Coins",
                [
                    "You don't have enough wallet coins."
                ]
            )
        )

    await ctx.send(
        view=BlackjackView(
            ctx.author,
            amount
        )
    )
@bot.hybrid_command(name="ping")
async def ping(ctx):

    latency = round(bot.latency * 1000)

    await ctx.send(
        view=create_view(
            "🏓 Pong",
            [
                f"Bot Ping: `{latency}ms`",
                "Made by **odxbrosky**"
            ]
        )
    )
@bot.hybrid_command(name="noprefix")
async def noprefix(ctx, member: discord.Member):

    if ctx.author.id not in OWNER_IDS:

        return await ctx.send(
            view=create_view(
                "❌ Owner Only",
                [
                    "Only the bot owner can use this command."
                ]
            )
        )

    users = load_no_prefix_users()

    if member.id in users:

        users.remove(member.id)

        status = "removed from"

    else:

        users.append(member.id)

        status = "added to"

    save_no_prefix_users(users)

    await ctx.send(
        view=create_view(
            "⚙️ No Prefix Updated",
            [
                f"{member.mention} has been **{status}** global no-prefix users."
            ]
        )
    )
class MinesView(ui.LayoutView):

    def __init__(self, player, amount):
        super().__init__(timeout=60)

        self.player = player
        self.amount = amount

        self.multiplier = 1.0

        # 2 random mines
        self.mines = random.sample(range(9), 2)

        self.clicked = []

        self.finished = False

        self.build()

    async def interaction_check(self, interaction):

        if interaction.user.id != self.player.id:

            await interaction.response.send_message(
                "This mines game is not yours.",
                ephemeral=True
            )

            return False

        return True

    def build(self):

        self.clear_items()

        rows = []

        for row in range(3):

            buttons = []

            for col in range(3):

                index = row * 3 + col

                if index in self.clicked:

                    btn = ui.Button(
                        label="💎",
                        style=discord.ButtonStyle.success,
                        disabled=True
                    )

                else:

                    btn = ui.Button(
                        label="❔",
                        style=discord.ButtonStyle.secondary
                    )

                    async def callback(interaction, i=index):
                        await self.pick(interaction, i)

                    btn.callback = callback

                buttons.append(btn)

            rows.append(
                ui.ActionRow(*buttons)
            )

        cashout = ui.Button(
            label=f"Cashout {self.multiplier:.1f}x",
            emoji="💸",
            style=discord.ButtonStyle.danger
        )

        cashout.callback = self.cash_out

        items = [
            ui.TextDisplay(
                f"## 💣 Mines\n"
                f"Player: {self.player.mention}\n"
                f"Bet: 🪙 `{self.amount}`\n"
                f"Multiplier: `{self.multiplier:.1f}x`"
            ),

            ui.Separator(
                spacing=discord.SeparatorSpacing.large,
                visible=True
            ),

            *rows,

            ui.ActionRow(cashout),

            ui.TextDisplay(
                "-# Vaultrix Mines • Components V2"
            )
        ]

        self.add_item(
            ui.Container(*items)
        )

    async def pick(self, interaction, index):

        if self.finished:
            return

        # mine hit
        if index in self.mines:

            self.finished = True

            user = get_user(self.player.id)

            user["wallet"] -= self.amount
            user["losses"] += 1
            user["streak"] = 0
            user["profit"] -= self.amount

            update_user(self.player.id, user)

            self.clear_items()

            self.add_item(
                ui.Container(
                    ui.TextDisplay(
                        f"## 💥 BOOM!\n"
                        f"You hit a mine.\n\n"
                        f"Lost: 🪙 `{self.amount}`\n"
                        f"Balance: 🪙 `{user['wallet']}`"
                    )
                )
            )

            return await interaction.response.edit_message(
                view=self
            )

        # safe tile
        self.clicked.append(index)

        self.multiplier += 0.4

        self.build()

        await interaction.response.edit_message(
            view=self
        )

    async def cash_out(self, interaction):

        if self.finished:
            return

        self.finished = True

        winnings = int(self.amount * self.multiplier)

        profit = winnings - self.amount

        user = get_user(self.player.id)

        user["wallet"] += profit
        user["wins"] += 1
        user["streak"] += 1
        user["profit"] += profit

        update_rank(user)

        update_user(self.player.id, user)

        self.clear_items()

        self.add_item(
            ui.Container(
                ui.TextDisplay(
                    f"## 💸 Cashout Successful\n"
                    f"Multiplier: `{self.multiplier:.1f}x`\n"
                    f"Profit: 🪙 `{profit}`\n"
                    f"Balance: 🪙 `{user['wallet']}`"
                )
            )
        )

        await interaction.response.edit_message(
            view=self
        )
@bot.hybrid_command(name="mines", aliases=['m'])
async def mines(ctx, amount: int):
    if not await check_channel(ctx):
        return
    if await block_if_loan_overdue(ctx):
        return

    user = get_user(ctx.author.id)

    if amount <= 0:

        return await ctx.send(
            view=create_view(
                "❌ Invalid Bet",
                [
                    "Bet amount must be above `0`."
                ]
            )
        )

    if amount > MAX_BET:

        return await ctx.send(
            view=create_view(
                "❌ Max Bet Reached",
                [
                    f"Max bet is 🪙 `{MAX_BET}`."
                ]
            )
        )

    if user["wallet"] < amount:

        return await ctx.send(
            view=create_view(
                "❌ Not Enough Coins",
                [
                    "You don't have enough wallet coins."
                ]
            )
        )

    await ctx.send(
        view=MinesView(
            ctx.author,
            amount
        )
    )
@bot.hybrid_command(name="crash")
async def crash(ctx, amount: int, cashout: float = 2.0):
    if not await check_channel(ctx):
        return
    if await block_if_loan_overdue(ctx):
        return
    user = get_user(ctx.author.id)

    if amount <= 0 or amount > MAX_BET or user["wallet"] < amount:
        return await ctx.send(view=create_view("❌ Invalid Bet", ["Check amount, max bet, or wallet balance."]))

    msg = await ctx.send(view=create_view("📈 Crash Starting", [f"Bet: 🪙 `{amount}`", f"Target: `{cashout}x`"]))

    crash_point = round(random.uniform(1.1, 5.0), 2)
    current = 1.0

    while current < cashout and current < crash_point:
        current = round(current + random.uniform(0.2, 0.5), 2)
        await msg.edit(view=create_view("📈 Crash Running", [f"Multiplier: `{current}x`", f"Target: `{cashout}x`"]))
        await asyncio.sleep(0.5)

    if cashout <= crash_point:
        profit = int(amount * cashout) - amount
        user["wallet"] += profit
        user["wins"] += 1
        user["profit"] += profit
        result = f"✅ Cashed out at `{cashout}x`\nProfit: 🪙 `{profit}`"
    else:
        user["wallet"] -= amount
        user["losses"] += 1
        user["profit"] -= amount
        result = f"💥 Crashed at `{crash_point}x`\nLost: 🪙 `{amount}`"

    update_user(ctx.author.id, user)

    await msg.edit(view=create_view("📈 Crash Result", [result, f"Balance: 🪙 `{user['wallet']}`"]))
@bot.hybrid_command(name="case", aliases=["open"])
async def case_open(ctx):
    user = get_user(ctx.author.id)
    cost = 1000

    if user["wallet"] < cost:
        return await ctx.send(view=create_view("❌ Not Enough Coins", [f"Case costs 🪙 `{cost}`."]))

    user["wallet"] -= cost

    rewards = [
        ("coins", 500),
        ("coins", 1500),
        ("coins", 3000),
        ("badge", "🎟️ Case Opener"),
        ("title", "Lucky Gambler")
    ]

    msg = await ctx.send(view=create_view("🎁 Opening Case", ["Spinning rewards..."]))

    for spin in ["🎟️", "💎", "🪙", "👑", "🎁"]:
        await msg.edit(view=create_view("🎁 Opening Case", [f"Reward rolling... {spin}"]))
        await asyncio.sleep(0.4)

    reward_type, reward_value = random.choice(rewards)

    if reward_type == "coins":
        user["wallet"] += reward_value
        text = f"You won 🪙 `{reward_value}` coins."
    elif reward_type == "badge":
        if reward_value not in user["badges"]:
            user["badges"].append(reward_value)
        text = f"You unlocked badge: {reward_value}"
    else:
        user["title"] = reward_value
        text = f"You unlocked title: **{reward_value}**"

    update_user(ctx.author.id, user)

    await msg.edit(view=create_view("🎁 Case Opened", [text, f"Balance: 🪙 `{user['wallet']}`"]))
class TowerView(ui.LayoutView):
    def __init__(self, player, amount):
        super().__init__(timeout=60)
        self.player = player
        self.amount = amount
        self.floor = 0
        self.multiplier = 1.0
        self.finished = False
        self.build()

    async def interaction_check(self, interaction):
        if interaction.user.id != self.player.id:
            await interaction.response.send_message("This tower game is not yours.", ephemeral=True)
            return False
        return True

    def build(self):
        self.clear_items()

        left = ui.Button(label="Left", emoji="⬅️", style=discord.ButtonStyle.secondary)
        mid = ui.Button(label="Middle", emoji="⬆️", style=discord.ButtonStyle.danger)
        right = ui.Button(label="Right", emoji="➡️", style=discord.ButtonStyle.secondary)
        cash = ui.Button(label=f"Cashout {self.multiplier:.1f}x", emoji="💸", style=discord.ButtonStyle.success)

        left.callback = lambda i: self.pick(i, "left")
        mid.callback = lambda i: self.pick(i, "middle")
        right.callback = lambda i: self.pick(i, "right")
        cash.callback = self.cashout

        self.add_item(
            ui.Container(
                ui.TextDisplay(
                    f"## 🗼 Tower Climb\n"
                    f"Player: {self.player.mention}\n"
                    f"Bet: 🪙 `{self.amount}`\n"
                    f"Floor: `{self.floor}`\n"
                    f"Multiplier: `{self.multiplier:.1f}x`"
                ),
                ui.Separator(spacing=discord.SeparatorSpacing.large, visible=True),
                ui.ActionRow(left, mid, right),
                ui.ActionRow(cash),
                ui.TextDisplay("-# Pick a path. One path is deadly.")
            )
        )

    async def pick(self, interaction, choice):
        trap = random.choice(["left", "middle", "right"])

        if choice == trap:
            user = get_user(self.player.id)
            user["wallet"] -= self.amount
            user["losses"] += 1
            update_user(self.player.id, user)

            self.clear_items()
            self.add_item(ui.Container(ui.TextDisplay(f"## 💥 Tower Failed\nYou picked **{choice}** and fell.\nLost: 🪙 `{self.amount}`\nBalance: `{user['wallet']}`")))
            return await interaction.response.edit_message(view=self)

        self.floor += 1
        self.multiplier += 0.5
        self.build()
        await interaction.response.edit_message(view=self)

    async def cashout(self, interaction):
        profit = int(self.amount * self.multiplier) - self.amount

        user = get_user(self.player.id)
        user["wallet"] += profit
        user["wins"] += 1
        update_user(self.player.id, user)

        self.clear_items()
        self.add_item(ui.Container(ui.TextDisplay(f"## 💸 Tower Cashout\nFloor: `{self.floor}`\nProfit: 🪙 `{profit}`\nBalance: `{user['wallet']}`")))
        await interaction.response.edit_message(view=self)


@bot.hybrid_command(name="tower")
async def tower(ctx, amount: int):
    if not await check_channel(ctx):
        return
    if await block_if_loan_overdue(ctx):
        return
    user = get_user(ctx.author.id)

    if amount <= 0 or amount > MAX_BET or user["wallet"] < amount:
        return await ctx.send(view=create_view("❌ Invalid Bet", ["Check amount, max bet, or wallet balance."]))

    await ctx.send(view=TowerView(ctx.author, amount))
@bot.hybrid_command(name="coinrain")
async def coinrain(ctx, amount: int = 500):

    if ctx.author.id not in OWNER_IDS:
        return await ctx.send(
            view=create_view(
                "❌ Owner Only",
                [
                    "Only the bot owner can start coin rain."
                ]
            )
        )

    bot.rain_amount = amount
    bot.rain_active = True

    await ctx.send(
        view=create_view(
            "🌧️ Coin Rain Event",
            [
                f"{ctx.author.mention} started a coin rain!",
                f"First user to type `claimrain` gets 🪙 `{amount}` coins.",
                "Made by **odxbrosky**"
            ]
        )
    )
@bot.hybrid_command(name="claimrain")
async def claimrain(ctx):

    if not getattr(bot, "rain_active", False):
        return await ctx.send(
            view=create_view(
                "❌ No Coin Rain",
                [
                    "No active coin rain event."
                ]
            )
        )

    user = get_user(ctx.author.id)
    amount = getattr(bot, "rain_amount", 500)

    user["wallet"] += amount
    update_user(ctx.author.id, user)

    bot.rain_active = False

    await ctx.send(
        view=create_view(
            "🌧️ Coin Rain Claimed",
            [
                f"{ctx.author.mention} claimed 🪙 `{amount}` coins!"
            ]
        )
    )
THEMES = {
    "crimson": {
        "name": "Crimson Neon",
        "emoji": "🟥",
        "footer": "Vaultrix Casino • Crimson Neon • Made by odxbrosky"
    },
    "cyan": {
        "name": "Cyber Cyan",
        "emoji": "🟦",
        "footer": "Vaultrix Casino • Cyber Cyan • Made by odxbrosky"
    },
    "gold": {
        "name": "Royal Gold",
        "emoji": "🟨",
        "footer": "Vaultrix Casino • Royal Gold • Made by odxbrosky"
    }
}

def get_theme(user_id):
    user = get_user(user_id)
    theme = user.get("theme", "crimson")
    return THEMES.get(theme, THEMES["crimson"])


def progress_bar(current, total, size=10):
    filled = int((current / total) * size)
    empty = size - filled
    return "█" * filled + "░" * empty


def neon_view(title, user_id, sections=None):
    sections = sections or []
    theme = get_theme(user_id)

    view = ui.LayoutView()

    items = [
        ui.TextDisplay(
            f"## {theme['emoji']} {title}"
        ),
        ui.Separator(
            spacing=discord.SeparatorSpacing.large,
            visible=True
        )
    ]

    for section in sections:
        if section and str(section).strip():
            items.append(ui.TextDisplay(str(section)))
            items.append(
                ui.Separator(
                    spacing=discord.SeparatorSpacing.large,
                    visible=True
                )
            )

    items.append(
        ui.TextDisplay(
            f"-# {theme['footer']}"
        )
    )

    view.add_item(ui.Container(*items))
    return view

def ensure_loan_fields(user):
    if "loan" not in user:
        user["loan"] = 0

    if "loan_due" not in user:
        user["loan_due"] = 0

    if "loan_overdue" not in user:
        user["loan_overdue"] = False

    if "loan_penalty_added" not in user:
        user["loan_penalty_added"] = False


def check_loan_status(user):
    ensure_loan_fields(user)

    now = int(time.time())

    if user["loan"] > 0 and user["loan_due"] > 0 and now > user["loan_due"]:
        user["loan_overdue"] = True

        if not user["loan_penalty_added"]:
            penalty = int(user["loan"] * LOAN_OVERDUE_PENALTY)
            user["loan"] += penalty
            user["loan_penalty_added"] = True

    return user
@bot.hybrid_command(name="loan")
async def loan(ctx, amount: int):
    user = get_user(ctx.author.id)
    ensure_loan_fields(user)

    if amount <= 0:
        return await ctx.send(
            view=create_view("❌ Invalid Loan", ["Loan amount must be above `0`."])
        )

    if user["loan"] + amount > LOAN_LIMIT:
        return await ctx.send(
            view=create_view(
                "❌ Loan Limit Reached",
                [
                    f"Max loan limit: 🪙 `{LOAN_LIMIT}`",
                    f"Current debt: 🪙 `{user['loan']}`"
                ]
            )
        )

    repay_amount = int(amount + (amount * LOAN_INTEREST_RATE))

    user["wallet"] += amount
    user["loan"] += repay_amount
    user["loan_due"] = int(time.time()) + LOAN_DUE_SECONDS
    user["loan_overdue"] = False
    user["loan_penalty_added"] = False

    update_user(ctx.author.id, user)

    await ctx.send(
        view=create_view(
            "🏦 Loan Approved",
            [
                f"Received: 🪙 `{amount}`",
                f"Debt with interest: 🪙 `{repay_amount}`",
                "Due in: `2 days`",
                "If unpaid after 2 days: `+10% penalty + gambling locked`"
            ]
        )
    )


@bot.hybrid_command(name="repay")
async def repay(ctx, amount: int):
    user = get_user(ctx.author.id)
    user = check_loan_status(user)

    if user["loan"] <= 0:
        return await ctx.send(
            view=create_view("✅ No Loan", ["You do not have any active loan."])
        )

    if amount <= 0:
        return await ctx.send(
            view=create_view("❌ Invalid Amount", ["Repay amount must be above `0`."])
        )

    if user["wallet"] < amount:
        return await ctx.send(
            view=create_view("❌ Not Enough Coins", ["You don't have enough wallet coins."])
        )

    amount = min(amount, user["loan"])

    user["wallet"] -= amount
    user["loan"] -= amount

    if user["loan"] <= 0:
        user["loan"] = 0
        user["loan_due"] = 0
        user["loan_overdue"] = False
        user["loan_penalty_added"] = False

    update_user(ctx.author.id, user)

    await ctx.send(
        view=create_view(
            "💳 Loan Repaid",
            [
                f"Paid: 🪙 `{amount}`",
                f"Remaining Debt: 🪙 `{user['loan']}`",
                f"Wallet: 🪙 `{user['wallet']}`"
            ]
        )
    )


@bot.hybrid_command(name="debt")
async def debt(ctx):
    user = get_user(ctx.author.id)
    user = check_loan_status(user)
    update_user(ctx.author.id, user)

    if user["loan"] <= 0:
        return await ctx.send(
            view=create_view("✅ No Debt", ["You do not have any active loan."])
        )

    now = int(time.time())
    left = user["loan_due"] - now

    if left > 0:
        time_left = f"{left // 86400}d {(left % 86400) // 3600}h"
    else:
        time_left = "OVERDUE"

    status = "🚨 OVERDUE" if user["loan_overdue"] else "✅ Active"

    await ctx.send(
        view=create_view(
            "📉 Debt Status",
            [
                f"Debt: 🪙 `{user['loan']}`",
                f"Status: {status}",
                f"Due: `{time_left}`"
            ]
        )
    )
async def block_if_loan_overdue(ctx):
    user = get_user(ctx.author.id)
    user = check_loan_status(user)
    update_user(ctx.author.id, user)

    if user["loan_overdue"]:
        await ctx.send(
            view=create_view(
                "🚫 Loan Overdue",
                [
                    "Your casino access is locked.",
                    f"Debt: 🪙 `{user['loan']}`",
                    "Use `repay <amount>` to unlock gambling."
                ]
            )
        )
        return True

    return False
BANK_INTEREST_RATE = 0.02
BANK_INTEREST_COOLDOWN = 3600


def ensure_interest_fields(user):

    if "last_interest" not in user:
        user["last_interest"] = 0


@bot.hybrid_command(name="interest")
async def interest(ctx):

    user = get_user(ctx.author.id)

    ensure_interest_fields(user)

    now = int(time.time())

    if now - user["last_interest"] < BANK_INTEREST_COOLDOWN:

        left = BANK_INTEREST_COOLDOWN - (
            now - user["last_interest"]
        )

        return await ctx.send(
            view=create_view(
                "⏳ Interest Cooldown",
                [
                    f"Come back in `{left // 60}m {left % 60}s`."
                ]
            )
        )

    if user["bank"] <= 0:

        return await ctx.send(
            view=create_view(
                "🏦 Empty Bank",
                [
                    "Deposit coins into your bank first."
                ]
            )
        )

    earned = int(
        user["bank"] * BANK_INTEREST_RATE
    )

    if earned <= 0:
        earned = 1

    user["bank"] += earned
    user["last_interest"] = now

    update_user(ctx.author.id, user)

    await ctx.send(
        view=create_view(
            "📈 Interest Claimed",
            [
                f"Interest Earned: 🪙 `{earned}`",
                f"New Bank Balance: 🏦 `{user['bank']}`",
                f"Rate: `{int(BANK_INTEREST_RATE * 100)}% per hour`"
            ]
        )
    )
@bot.hybrid_command(name="setchannel")
async def setchannel(ctx, channel: discord.TextChannel):

    if ctx.author.id not in OWNER_IDS:

        return await ctx.send(
            view=create_view(
                "❌ Owner Only",
                [
                    "Only bot owners can set the bot channel."
                ]
            )
        )

    data = load_channels()

    data[str(ctx.guild.id)] = channel.id

    save_channels(data)

    await ctx.send(
        view=create_view(
            "📌 Bot Channel Set",
            [
                f"Bot commands are now restricted to {channel.mention}."
            ]
        )
    )
@bot.hybrid_command(name="removechannel")
async def removechannel(ctx):

    if ctx.author.id not in OWNER_IDS:

        return await ctx.send(
            view=create_view(
                "❌ Owner Only",
                [
                    "Only bot owners can remove the bot channel."
                ]
            )
        )

    data = load_channels()

    if str(ctx.guild.id) in data:
        del data[str(ctx.guild.id)]

    save_channels(data)

    await ctx.send(
        view=create_view(
            "♻️ Channel Restriction Removed",
            [
                "Bot can now be used in all channels."
            ]
        )
    ) 
# =========================
# RUN
# =========================

bot.run(TOKEN)