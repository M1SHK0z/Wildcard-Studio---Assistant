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


# ---------------- DISCORD ----------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print("Ready")
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))


# ---------------- FAST SEND FUNCTION ----------------
def fast_post(url, payload):
    try:
        requests.post(url, json=payload, timeout=2)  # 🔥 FAST timeout
        return True
    except:
        return False


# ---------------- /MESSAGE ----------------
@bot.tree.command(name="message", guild=discord.Object(id=GUILD_ID))
async def message(interaction: discord.Interaction, text: str):

    ok = fast_post(BASE_URL + "/push_payload", {
        "type": "message",
        "content": text,
        "author": interaction.user.name
    })

    if ok:
        embed = discord.Embed(
            title="Success",
            description="Message sent successfully",
            color=discord.Color.green()
        )
        embed.add_field(name="Content", value=text, inline=False)
    else:
        embed = discord.Embed(
            title="Failed",
            description="Message failed",
            color=discord.Color.red()
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ---------------- /GAMEBAN ----------------
@bot.tree.command(name="gameban", guild=discord.Object(id=GUILD_ID))
async def gameban(interaction: discord.Interaction, username: str, action: str, duration: str = None):

    ok = fast_post(BASE_URL + "/push_command", {
        "type": "gameban",
        "user": username,
        "action": action,
        "duration": duration
    })

    if ok:
        embed = discord.Embed(
            title="Success",
            description="Command sent successfully",
            color=discord.Color.green()
        )
        embed.add_field(name="User", value=username, inline=True)
        embed.add_field(name="Action", value=action, inline=True)
    else:
        embed = discord.Embed(
            title="Failed",
            description="Command failed",
            color=discord.Color.red()
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ---------------- START ----------------
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)
