import os
import discord
from discord.ext import commands
from flask import Flask, request, jsonify
import threading

TOKEN = os.environ["DISCORD_BOT_TOKEN"]

CHANNEL_ID = 1497247654977994752
GUILD_ID = 1497246825646788650

ROBLOX_ENDPOINT = "https://your-server-url/pop_payload"

# -------- DISCORD --------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -------- QUEUE --------
payload_queue = []

# -------- FLASK --------
app = Flask(__name__)

@app.route("/pop_payload", methods=["GET"])
def pop_payload():
    if payload_queue:
        return jsonify(payload_queue.pop(0)), 200
    return jsonify({}), 200

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# -------- DISCORD LISTENER --------
@bot.event
async def on_message(msg: discord.Message):
    if msg.author.bot:
        return
    
    if msg.channel.id != CHANNEL_ID:
        return

    try:
        data = {
            "content": msg.content,
            "author": str(msg.author)
        }

        payload_queue.append(data)

        embed = discord.Embed(
            title="Sent",
            description="Message sent successfully",
            color=discord.Color.green()
        )
    except Exception as e:
        print(e)
        embed = discord.Embed(
            title="Failed",
            description="Failed to send",
            color=discord.Color.red()
        )

    await msg.channel.send(embed=embed)

# -------- START --------
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)
