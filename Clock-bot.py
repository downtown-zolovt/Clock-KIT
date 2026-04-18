import os
import discord
from discord.ext import commands

# Railway will inject 'DISCORD_TOKEN' into the environment
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is back online via Railway!')

@bot.command()
async def status(ctx):
    await ctx.send("Systems operational. Ready for playblasts!")

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ ERROR: DISCORD_TOKEN variable is missing in Railway!")
