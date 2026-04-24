import os
import discord
from discord.ext import commands
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

# 1. SETUP
TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

# FORCE CONFIG
genai.configure(api_key=GEMINI_KEY, transport='rest')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_ai_response(prompt, img_data=None):
    # CRITICAL CHANGE: Using the explicit 'models/gemini-1.5-flash' path
    # Some Free Tier keys require this full string to bypass the v1beta 404
    model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
    
    if img_data:
        response = model.generate_content([prompt, img_data])
    else:
        response = model.generate_content(prompt)
    return response.text

@bot.event
async def on_ready():
    print(f'✅ {bot.user} online.')
    # Diagnostic: Check what models this key can actually see
    print("Checking available models...")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"FOUND: {m.name}")
    except Exception as e:
        print(f"Diagnostic failed: {e}")

@bot.event
async def on_message(message):
    if message.author.bot: return

    if bot.user.mentioned_in(message) or message.content.startswith('!debug'):
        async with message.channel.typing():
            clean_text = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').replace('!debug', '').strip()
            if not clean_text: clean_text = "Checking system endpoint stability."

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
                # If it's STILL a NotFound, check the Railway logs for the "FOUND:" prints
                await message.reply(f"❌ Connection Error: {str(e)}")

    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(TOKEN)
