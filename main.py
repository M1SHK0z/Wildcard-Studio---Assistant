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
server_players = []

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


# ---------------- COMMANDS (GAMEBAN) ----------------
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


# ---------------- PLAYERS LIST ----------------
@app.route("/push_players", methods=["POST"])
def push_players():
    global server_players
    data = request.get_json()
    server_players = data.get("players", [])
    return jsonify({"ok": True})


@app.route("/pop_players", methods=["GET"])
def pop_players():
    return jsonify({"players": server_players})


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


# ---------------- DISCORD ----------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("Logged in")
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))


# ---------------- MESSAGE ----------------
@bot.tree.command(name="message", guild=discord.Object(id=GUILD_ID))
async def message(interaction: discord.Interaction, text: str):
    requests.post(BASE_URL + "/push_payload", json={
        "type": "message",
        "content": text,
        "author": interaction.user.name
    })

    await interaction.response.send_message("Sent", ephemeral=True)


# ---------------- GAMEBAN COMMAND ----------------
@bot.tree.command(name="gameban", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(username="Player", action="ban/unban/temp", duration="Only temp")
@app_commands.choices(
    action=[
        app_commands.Choice(name="Ban", value="ban"),
        app_commands.Choice(name="Unban", value="unban"),
        app_commands.Choice(name="Temp", value="temp")
    ],
    duration=[
        app_commands.Choice(name="1 Day", value="1d"),
        app_commands.Choice(name="7 Days", value="7d"),
        app_commands.Choice(name="30 Days", value="30d")
    ]
)
async def gameban(interaction: discord.Interaction, username: str, action: app_commands.Choice[str], duration: app_commands.Choice[str] = None):

    requests.post(BASE_URL + "/push_command", json={
        "type": "gameban",
        "user": username,
        "action": action.value,
        "duration": duration.value if duration else None
    })

    await interaction.response.send_message(f"Sent {action.value} for {username}", ephemeral=True)


if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)
