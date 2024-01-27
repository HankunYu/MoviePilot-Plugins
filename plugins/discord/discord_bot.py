import discord, discord.webhook, asyncio, os
from discord.ext import commands
import plugins.discord.tokenes as tokenes
from app.log import logger

on_conversion = False
current_channel = None
intents = discord.Intents.all()
client = commands.Bot(command_prefix='$', intents=intents)

# Load cogs
async def load_extensions():
    try:
        await client.load_extension(f"plugins.discord.cogs.moviepilot_cog")
    except Exception as e:
        logger.error(f"Cog 加载失败: {e}")

# Unload cogs
async def unload_extensions():
    try:
        await client.unload_extension(f"plugins.discord.cogs.moviepilot_cog")
    except Exception as e:
        logger.error(f"Cog 卸载失败: {e}")

# Run bot
async def run_bot():
    async with client:
        if tokenes.is_bot_running:
            logger.info("Discord bot 已启动")
        else:
            try:
                logger.info("Discord bot 启动中...")
                await load_extensions()
                await client.start(tokenes.bot_token)
                tokenes.is_bot_running = True
            except Exception as e:
                logger.error(f"Discord bot 启动失败: {e}")

    
async def stop():
    if tokenes.is_bot_running == True:
        logger.info("Discord bot 停止中...")
        async with client:
            try:
                tokenes.is_bot_running = False
                await client.close()
            except Exception as e:
                logger.error(f"Discord bot 停止失败: {e}")
