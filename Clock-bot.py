import os
import discord
from discord.ext import commands
from google import genai
from google.genai import types

# 1. SETUP
# These must be set in your Railway 'Variables' tab
TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

# Initialize the AI Client
client = genai.Client(api_key=GEMINI_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 2. THE CHAT LOGIC
@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online and connected to Gemini!')

@bot.event
async def on_message(message):
    # Ignore the bot's own messages
    if message.author.bot:
        return

    # Trigger: When someone mentions the bot
    if bot.user.mentioned_in(message):
        async with message.channel.typing():
            # Clean up the message (remove the @mention)
            user_text = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
            
            if not user_text:
                user_text = "Hello!"

            try:
                # We use the most stable model string for the v1 API
                response = client.models.generate_content(
                    model="gemini-1.5-flash", 
                    contents=user_text
                )
                await message.reply(response.text)
            except Exception as e:
                await message.reply(f"❌ Connection Error: {str(e)}")

    # Allow other !commands to work
    await bot.process_commands(message)

@bot.command()
async def status(ctx):
    await ctx.send("Bot is alive! Mention me to chat.")

if __name__ == "__main__":
    if TOKEN and GEMINI_KEY:
        bot.run(TOKEN)
    else:
        print("❌ ERROR: Missing DISCORD_TOKEN or GEMINI_API_KEY in Railway Variables!")
