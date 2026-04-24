import os
import discord
from discord.ext import commands
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

# 1. SETUP
TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

# --- FIX START: Force Production API Version ---
# This overrides the 'v1beta' default that was causing the 404
genai.configure(
    api_key=GEMINI_KEY,
    transport='rest' # Using REST transport is often more stable for cloud hosts
)
# --- FIX END ---

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 2. UPDATED CHAT FUNCTION
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_ai_response(prompt, img_data=None):
    # We use the generic 'gemini-1.5-flash' name. 
    # The SDK will now route this through v1 instead of v1beta.
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    if img_data:
        response = model.generate_content([prompt, img_data])
    else:
        response = model.generate_content(prompt)
    return response.text

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online. Routing via Production API v1.')

@bot.event
async def on_message(message):
    if message.author.bot: return

    if bot.user.mentioned_in(message) or message.content.startswith('!debug'):
        async with message.channel.typing():
            # Handle mention formats for both Mobile and Desktop
            clean_text = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').replace('!debug', '').strip()
            if not clean_text: clean_text = "Analyze current system status."

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
                # This will now catch and show if the error moved from 404 to something else
                await message.reply(f"❌ Connection Error: {str(e)}")

    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(TOKEN)
