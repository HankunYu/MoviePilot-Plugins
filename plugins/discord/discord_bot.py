import discord, re, discord.webhook, asyncio, os
from discord import app_commands
from discord.ext import commands
import plugins.discord.tokenes as tokenes
"""
bot 本体.
"""

on_conversion = False
current_channel = None
intents = discord.Intents.all()
client = commands.Bot(command_prefix='$', intents=intents)

# Load cogs
async def load_extensions():
    await client.load_extension("plugins.discord.cogs.moviepilot_cog")

async def run_bot():
    async with client:
        await load_extensions()
        await client.start(tokenes.bot_token)

