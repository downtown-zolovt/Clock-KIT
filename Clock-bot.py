import os
import asyncio
import discord
from discord.ext import commands
from google import genai
from google.genai import types

# 1. SETUP
TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

# Initialize the NEW Google GenAI Client
client = genai.Client(api_key=GEMINI_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 2. THE GENERATION LOGIC
def get_ai_response(prompt, img_bytes=None):
    # Using the 2.0 model confirmed in your logs
    model_id = "gemini-2.0-flash" 
    
    contents = [prompt]
    if img_bytes:
        contents.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))

    # This is a synchronous call to the SDK
    response = client.models.generate_content(
        model=model_id,
        contents=contents
    )
    return response.text

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online using google-genai 1.0+')

@bot.command()
async def debug(ctx):
    """Explicit command to prevent 'CommandNotFound' errors in logs."""
    await ctx.send("Systems operational. Gemini 2.0-Flash is standing by.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Handle mentions or !debug
    if bot.user.mentioned_in(message) or message.content.startswith('!debug'):
        async with message.channel.typing():
            # Clean up message text
            clean_text = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').replace('!debug', '').strip()
            if not clean_text: 
                clean_text = "System check: Awaiting instructions."

            img_data = None
            if message.attachments:
                for attachment in message.attachments:
                    if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg']):
                        img_data = await attachment.read()
                        break 

            try:
                # --- THE FIX ---
                # We use asyncio.to_thread to run the blocking get_ai_response function
                # without freezing the whole bot. We MUST 'await' the result.
                reply = await asyncio.to_thread(get_ai_response, clean_text, img_data)
                
                await message.reply(reply)
            except Exception as e:
                await message.reply(f"❌ API Error: {str(e)}")

    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(TOKEN)
