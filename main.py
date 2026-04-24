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
queue_lock = threading.Lock()

# ---------------- FLASK ----------------
@app.route("/push_payload", methods=["POST"])
def push_payload():
    try:
        data = request.get_json()

        with queue_lock:
            payload_queue.append(data)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("push error:", e)
        return jsonify({"status": "error"}), 400


@app.route("/pop_payload", methods=["GET"])
def pop_payload():
    with queue_lock:
        if payload_queue:
            return jsonify(payload_queue.pop(0)), 200
        return jsonify({}), 200


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ---------------- DISCORD ----------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))

# ---------------- MESSAGE COMMAND ----------------
@bot.tree.command(
    name="message",
    description="Send message to Roblox",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(text="Message to send")
async def message(interaction: discord.Interaction, text: str):
    try:
        payload = {
            "id": str(uuid.uuid4()),
            "type": "message",
            "content": text,
            "author": str(interaction.user)
        }

        r = requests.post(
            BASE_URL + "/push_payload",
            json=payload,
            timeout=10
        )

        if r.status_code != 200:
            raise Exception(f"HTTP {r.status_code}")

        embed = discord.Embed(
            title="Success",
            description="Message sent successfully",
            color=discord.Color.green()
        )
        embed.add_field(name="Content", value=text, inline=False)

    except Exception as e:
        print("ERROR:", e)

        embed = discord.Embed(
            title="Failed",
            description=str(e),
            color=discord.Color.red()
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)

# ---------------- START ----------------
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)
