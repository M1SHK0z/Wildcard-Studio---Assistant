import os
import discord
from discord import app_commands
from discord.ext import commands
import threading
from flask import Flask, request, jsonify
import requests
import uuid

TOKEN = os.environ["DISCORD_BOT_TOKEN"]
GUILD_ID = 1497246825646788650

BASE_URL = "https://wildcard-studio-assistant.onrender.com"

app = Flask(__name__)

payload_queue = []
command_queue = []
lock = threading.Lock()

# ---------------- FLASK ----------------
@app.route("/push_payload", methods=["POST"])
def push_payload():
    data = request.get_json()
    with lock:
        payload_queue.append(data)
    return jsonify({"ok": True})


@app.route("/pop_payload", methods=["GET"])
def pop_payload():
    with lock:
        return jsonify(payload_queue.pop(0) if payload_queue else {})


@app.route("/push_command", methods=["POST"])
def push_command():
    data = request.get_json()
    with lock:
        command_queue.append(data)
    return jsonify({"ok": True})


@app.route("/pop_command", methods=["GET"])
def pop_command():
    with lock:
        return jsonify(command_queue.pop(0) if command_queue else {})


def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


# ---------------- DISCORD SETUP ----------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print("Bot Ready")
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))


# ---------------- /MESSAGE ----------------
@bot.tree.command(name="message", guild=discord.Object(id=GUILD_ID))
async def message(interaction: discord.Interaction, text: str):

    ok = True
    try:
        requests.post(BASE_URL + "/push_payload", json={
            "type": "message",
            "content": text,
            "author": interaction.user.name
        }, timeout=2)
    except:
        ok = False

    if ok:
        embed = discord.Embed(title="Success", description="Message Sent Successfully", color=0x2ecc71)
    else:
        embed = discord.Embed(title="Failed", description="Message Failed", color=0xe74c3c)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ---------------- /GAMEBAN ----------------
@bot.tree.command(name="gameban", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    username="Player username",
    action="Ban / Unban / Temporarily",
    duration="Only used for Temporarily"
)
@app_commands.choices(
    action=[
        app_commands.Choice(name="Ban", value="ban"),
        app_commands.Choice(name="Unban", value="unban"),
        app_commands.Choice(name="Temporarily", value="temp")
    ],
    duration=[
        app_commands.Choice(name="1 Day", value="1d"),
        app_commands.Choice(name="7 Days", value="7d"),
        app_commands.Choice(name="30 Days", value="30d"),
        app_commands.Choice(name="Permanent", value="perm")
    ]
)
async def gameban(
    interaction: discord.Interaction,
    username: str,
    action: app_commands.Choice[str],
    duration: app_commands.Choice[str] = None
):

    ok = True

    try:
        payload = {
            "type": "gameban",
            "user": username,
            "action": action.value,
            "duration": duration.value if action.value == "temp" and duration else None
        }

        requests.post(BASE_URL + "/push_command", json=payload, timeout=2)

    except:
        ok = False

    if ok:
        embed = discord.Embed(title="Success", color=0x2ecc71)
        embed.add_field(name="User", value=username, inline=True)
        embed.add_field(name="Action", value=action.value, inline=True)
    else:
        embed = discord.Embed(title="Failed", color=0xe74c3c)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ---------------- START ----------------
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)
