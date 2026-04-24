import os
import discord
from discord.ext import commands
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

# 1. SETUP
TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

# --- FORCED PRODUCTION CONFIG ---
# This forces the API to use the stable 'v1' route instead of 'v1beta'
genai.configure(
    api_key=GEMINI_KEY,
    transport='rest'
)
# -------------------------------

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_ai_response(prompt, img_data=None):
    # 'gemini-1.5-flash' is the stable production string
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    if img_data:
        response = model.generate_content([prompt, img_data])
    else:
        response = model.generate_content(prompt)
    return response.text

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online. Routing via Production API.')

@bot.event
async def on_message(message):
    if message.author.bot: return

    if bot.user.mentioned_in(message) or message.content.startswith('!debug'):
        async with message.channel.typing():
            # Clean up the message text
            clean_text = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').replace('!debug', '').strip()
            if not clean_text: clean_text = "System check: Are you active?"

            img_part = None
            if message.attachments:
                for attachment in message.attachments:
                    if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg']):
                        raw_data = await attachment.read()
                        img_part = {'mime_type': attachment.content_type, 'data': raw_data}

            try:
                reply = get_ai_response(clean_text, img_part)
                await message.reply(reply)
            except Exception as e:
                # If this hits, the error will tell us if it's still a 404 or a 429 (Rate Limit)
                await message.reply(f"❌ Connection Error: {str(e)}")

    await bot.process_commands(message)

if __name__ == "__main__":
    if not GEMINI_KEY:
        print("❌ CRITICAL: GEMINI_API_KEY is missing from environment variables!")
    bot.run(TOKEN)
