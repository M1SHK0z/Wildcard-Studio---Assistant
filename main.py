import discord
from discord import app_commands
from discord.ext import commands
import os

import firebase_admin
from firebase_admin import credentials, db

# === ENV ===
TOKEN = os.getenv("DISCORD_TOKEN")

# === CONFIG ===
GUILD_ID = 1497246825646788650
SWORD_CHANNEL_ID = 1497247654977994752
VALUE_CHANNEL_ID = 1497246975698014359
LOG_CHANNEL_ID = 1497246827567775816

# === FIREBASE INIT ===
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://sword-value-default-rtdb.europe-west1.firebasedatabase.app/"
})

DB = db.reference("swords")

# === FALLBACK IMAGE ===
FALLBACK_IMAGE = "https://cdn.discordapp.com/attachments/808417839332982805/1485418871799283835/sword.png"

# === DEFAULT DATA ===
DEFAULT_SWORDS = {
    "test sword": {
        "value": "99999999999",
        "demand": "Extremely High!",
        "description": "None",
        "image": ""
    },
    "Trophy V3": {
        "value": "6000000",
        "demand": "High",
        "description": "None",
        "image": "https://cdn.discordapp.com/attachments/1017411708362432583/1499473605174759636/v3.png"
    },
    "Trophy V2": {
        "value": "7000001",
        "demand": "High",
        "description": "None",
        "image": "https://cdn.discordapp.com/attachments/808417839332982805/1498861849293226044/sword.png"
    },
    "Toxic Sword": {
        "value": "100000",
        "demand": "Low",
        "description": "None",
        "image": "https://cdn.discordapp.com/attachments/808417839332982805/1495384052247826554/sword.png"
    },
    "Reaper Scythe": {
        "value": "8000000",
        "demand": "Extremely High",
        "description": "None",
        "image": "https://cdn.discordapp.com/attachments/808417839332982805/1498249293432230039/sword.png"
    },
    "Trophy": {
        "value": "1000000",
        "demand": "High",
        "description": "None",
        "image": "https://cdn.discordapp.com/attachments/808417839332982805/1499479353707462759/sword.png"
    },
}

# === DATABASE HELPERS ===
def get_all():
    data = DB.get()
    return data if data else {}

def get_one(name):
    return DB.child(name).get()

def update_one(name, data):
    DB.child(name).update(data)

def ensure_defaults():
    current = DB.get()

    if not current:
        DB.set(DEFAULT_SWORDS)
        return

    # Only add missing swords (does NOT overwrite existing)
    for name, data in DEFAULT_SWORDS.items():
        if name not in current:
            DB.child(name).set(data)

# === BOT SETUP ===
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# === CHANNEL CHECK ===
async def check_channel(interaction, channel_id):
    if interaction.channel_id != channel_id:
        await interaction.response.send_message(
            f"❌ Use this in <#{channel_id}>",
            ephemeral=True
        )
        return False
    return True

# === AUTOCOMPLETE ===
async def name_autocomplete(interaction, current: str):
    swords = get_all()
    return [
        app_commands.Choice(name=n, value=n)
        for n in swords.keys()
        if current.lower() in n.lower()
    ]

# === /SWORD ===
@bot.tree.command(name="sword", description="Show sword info", guild=discord.Object(id=GUILD_ID))
@app_commands.autocomplete(name=name_autocomplete)
async def sword(interaction: discord.Interaction, name: str):

    if not await check_channel(interaction, SWORD_CHANNEL_ID):
        return

    data = get_one(name)

    if not data:
        await interaction.response.send_message("Sword not found.", ephemeral=True)
        return

    raw_value = data.get("value") or "0"

    try:
        value = f"{int(raw_value):,}"
    except:
        value = raw_value

    embed = discord.Embed(title=name, color=discord.Color(0x0099FF))
    embed.add_field(name="Value", value=value, inline=True)
    embed.add_field(name="Demand", value=data.get("demand", "Unknown"), inline=True)
    embed.add_field(name="Description", value=data.get("description", "None"), inline=False)
    embed.set_image(url=data.get("image") or FALLBACK_IMAGE)

    await interaction.response.send_message(embed=embed)

# === /VALUE ===
@bot.tree.command(name="value", description="Change value", guild=discord.Object(id=GUILD_ID))
@app_commands.autocomplete(name=name_autocomplete)
async def value(interaction: discord.Interaction, name: str, new_value: str):

    if not await check_channel(interaction, VALUE_CHANNEL_ID):
        return

    role = discord.utils.get(interaction.user.roles, name="Value Adjuster")

    if role is None:
        await interaction.response.send_message("❌ No permission.", ephemeral=True)
        return

    data = get_one(name)

    if not data:
        await interaction.response.send_message("Sword not found.", ephemeral=True)
        return

    update_one(name, {"value": new_value})

    try:
        new_display = f"{int(new_value):,}"
    except:
        new_display = new_value

    embed = discord.Embed(
        title="✅ Value Adjusted",
        description=f"{interaction.user.mention} updated **{name}** → **{new_display}**",
        color=discord.Color.green()
    )

    embed.set_thumbnail(url=data.get("image") or FALLBACK_IMAGE)

    log = bot.get_channel(LOG_CHANNEL_ID)
    if log:
        await log.send(embed=embed)

    await interaction.response.send_message(
        embed=discord.Embed(
            title="Successful",
            description=f"{name} updated.",
            color=discord.Color.green()
        )
    )

# === READY ===
@bot.event
async def on_ready():
    ensure_defaults()
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Logged in as {bot.user}")

# === RUN ===
bot.run(TOKEN)
