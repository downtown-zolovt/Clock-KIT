import os
import discord
from discord.ext import commands
from google import genai
from google.genai import types

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

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is now an AI Assistant on Railway!')

@bot.command()
async def status(ctx):
    await ctx.send("Systems operational. AI Debugger is active!")

# 2. AI LOGIC (Handles mentions and images)
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Trigger if the bot is mentioned OR starts with !debug
    if bot.user.mentioned_in(message) or message.content.startswith('!debug'):
        async with message.channel.typing():
            # Extract the text prompt
            prompt = message.content.replace(f'<@!{bot.user.id}>', '').replace('!debug', '').strip()
            if not prompt:
                prompt = "Analyze this content for errors."

            contents = [prompt]

            # Process Attachments (Screenshots of errors)
            if message.attachments:
                for attachment in message.attachments:
                    if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg', 'webp']):
                        img_bytes = await attachment.read()
                        contents.append(types.Part.from_bytes(
                            data=img_bytes,
                            mime_type=attachment.content_type
                        ))

            try:
                # Call Gemini 2.0 Flash
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        tools=[types.Tool(code_execution=types.ToolCodeExecution())]
                    )
                )
                
                # Reply to the user
                await message.reply(response.text)

            except Exception as e:
                await message.reply(f"❌ AI Error: {str(e)}")

    # Crucial for allowing @bot.command() to still work
    await bot.process_commands(message)

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ ERROR: DISCORD_TOKEN variable is missing in Railway!")
