import discord, discord.webhook, asyncio, os
from discord.ext import commands
import plugins.discord.tokenes as tokenes
from app.log import logger
"""
bot 本体.
"""

on_conversion = False
current_channel = None
intents = discord.Intents.all()
client = commands.Bot(command_prefix='$', intents=intents)

# Load cogs
async def load_extensions():
    for filename in os.listdir(os.getcwd() + "/cogs"):
        logger.info(f"Loading {filename}")  
        if filename.endswith(".py"):
            await client.load_extension(f"cogs.{filename[:-3]}")

async def run_bot():
    async with client:
        await load_extensions()
        await client.start(tokenes.bot_token)

