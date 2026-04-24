import os
import discord
from discord.ext import commands
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

# 1. AUTHENTICATION
TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

client = genai.Client(api_key=GEMINI_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SYSTEM_PROMPT = "You are the AI brain of 'Clock-kit', a 3D pipeline expert for Blender and Houdini."

# 2. THE ROBUST FALLBACK LOGIC
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=6),
    reraise=True
)
def get_ai_response(content_list):
    # We try these three variants because different SDK versions prefer different strings
    model_variants = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "flash-1.5"]
    
    last_error = None
    for model_name in model_variants:
        try:
            return client.models.generate_content(
                model=model_name,
                contents=content_list,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    tools=[types.Tool(code_execution=types.ToolCodeExecution())]
                )
            )
        except Exception as e:
            last_error = e
            # Only continue to the next model if the error is a 404 (Not Found)
            if "404" in str(e):
                print(f"⚠️ Model variant {model_name} failed with 404, trying next...")
                continue
            # If it's a 429 (Quota) or 401 (Auth), stop and raise it
            raise e
            
    raise last_error

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online. Running fallback-ready model check.')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user.mentioned_in(message) or message.content.startswith('!debug'):
        async with message.channel.typing():
            prompt = message.content.replace(f'<@!{bot.user.id}>', '').replace('!debug', '').strip()
            contents = [prompt if prompt else "Analyze this."]

            # Handle Attachments
            if message.attachments:
                for attachment in message.attachments:
                    if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg']):
                        img_bytes = await attachment.read()
                        contents.append(types.Part.from_bytes(data=img_bytes, mime_type=attachment.content_type))

            try:
                response = get_ai_response(contents)
                await message.reply(response.text)
            except Exception as e:
                await message.reply(f"❌ AI Connection Error: {str(e)}")

    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(TOKEN)
