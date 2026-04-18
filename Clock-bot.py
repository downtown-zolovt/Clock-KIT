import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# === Bypass timer ===
app = Flask('')

@app.route('/')
def home():
    return "Test Bot is Online!"

def run_flask():
    # Render uses port 8080 or 10000 by default
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# === CONFIG ===
# ngambil token dari Env yang udah di bikin di web render
TOKEN = os.environ.get('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    print("Test mode active: Send '!ping' in Discord to check me!")

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong! I am alive on Render!")

# Start the 'heartbeat' for Render
keep_alive()

# Start the bot
if TOKEN:
    bot.run(TOKEN)
else:
    print("ERROR: No DISCORD_TOKEN found in Environment Variables!")
