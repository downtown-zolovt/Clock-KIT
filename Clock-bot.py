import os
import discord
from discord.ext import commands
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# 1. AUTHENTICATION
TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

# Initialize the AI Client
client = genai.Client(api_key=GEMINI_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SYSTEM_PROMPT = """
You are the AI brain of 'Clock-kit'. Your expertise is in Blender (bpy), 
Houdini (hou), and Python automation. Help the user debug 3D pipeline scripts. 
If an image is provided, it's a console error screenshot—find the fix.
"""

# 2. RETRY LOGIC
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
def get_ai_response(content_list):
    return client.models.generate_content(
        model="flash-1.5", 
        contents=content_list,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[types.Tool(code_execution=types.ToolCodeExecution())]
        )
    )

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is active on Gemini 1.5 Flash (Railway)')

@bot.command()
async def status(ctx):
    await ctx.send("Systems operational. Using Gemini 1.5 Flash!")

@bot.command()
async def reset(ctx):
    """Clears the current session context (useful if the AI is 'stuck' on an old error)"""
    await ctx.send("Context cleared. Ready for a fresh 3D debugging session!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Trigger if mentioned OR starts with !debug
    if bot.user.mentioned_in(message) or message.content.startswith('!debug'):
        async with message.channel.typing():
            prompt = message.content.replace(f'<@!{bot.user.id}>', '').replace('!debug', '').strip()
            if not prompt:
                prompt = "Analyze this content for errors."

            contents = [prompt]

            if message.attachments:
                for attachment in message.attachments:
                    if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg', 'webp']):
                        img_bytes = await attachment.read()
                        contents.append(types.Part.from_bytes(
                            data=img_bytes,
                            mime_type=attachment.content_type
                        ))

            try:
                response = get_ai_response(contents)
                await message.reply(response.text)
            except Exception as e:
                await message.reply(f"❌ AI Error: {str(e)}")

    await bot.process_commands(message)

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ ERROR: DISCORD_TOKEN variable is missing in Railway!")
