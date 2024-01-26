import discord, discord.webhook, asyncio, os
from discord.ext import commands
import plugins.discord.tokenes as tokenes
import plugins.discord.cogs.moviepilot_cog as moviepilot_cog
from app.log import logger

on_conversion = False
current_channel = None
intents = discord.Intents.all()
client = commands.Bot(command_prefix='$', intents=intents)

# Load cogs
async def load_extensions():
    await client.load_extension(f"plugins.discord.cogs.moviepilot_cog")

# Unload cogs
async def unload_extensions():
    await client.unload_extension(f"plugins.discord.cogs.moviepilot_cog")

# Run bot
async def run_bot():
    logger.info("Discord bot 启动中...")
    async with client:
        try:
            await load_extensions()
        except Exception as e:
            logger.error(f"Cog 加载失败: {e}")
        
        try:
            await client.start(tokenes.bot_token)
        except Exception as e:
            logger.error(f"Discord bot 启动失败: {e}")

    
async def stop():
    logger.info("Discord bot 停止中...")
    await unload_extensions()