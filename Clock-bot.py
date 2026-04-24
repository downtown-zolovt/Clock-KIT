import os
import discord
from discord.ext import commands
import google.generativeai as genai # Switched to the more stable library
from tenacity import retry, stop_after_attempt, wait_exponential

# 1. SETUP
TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

# Configure the SDK
genai.configure(api_key=GEMINI_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 2. THE STABLE CHAT FUNCTION
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_ai_response(prompt, img_data=None):
    # Using the 'models/' prefix explicitly often fixes the 404 on Free Tier
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    if img_data:
        response = model.generate_content([prompt, img_data])
    else:
        response = model.generate_content(prompt)
    return response.text

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online and using the Stable SDK.')

@bot.event
async def on_message(message):
    if message.author.bot: return

    if bot.user.mentioned_in(message) or message.content.startswith('!debug'):
        async with message.channel.typing():
            clean_text = message.content.replace(f'<@!{bot.user.id}>', '').replace('!debug', '').strip()
            if not clean_text: clean_text = "Checking systems..."

            img_part = None
            if message.attachments:
                for attachment in message.attachments:
                    if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg']):
                        raw_data = await attachment.read()
                        img_part = {'mime_type': 'image/jpeg', 'data': raw_data}

            try:
                reply = get_ai_response(clean_text, img_part)
                await message.reply(reply)
            except Exception as e:
                # If it STILL 404s, we will know exactly why now
                await message.reply(f"❌ SDK Error: {str(e)}")

    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(TOKEN)
