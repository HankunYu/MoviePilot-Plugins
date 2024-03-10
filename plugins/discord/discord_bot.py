import discord, discord.webhook, asyncio, os, sys
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
        logger.info("Cog 加载完成")
    except Exception as e:
        logger.error(f"Cog 加载失败: {e}")

# Unload cogs
async def unload_extensions():
    try:
        await client.unload_extension(f"plugins.discord.cogs.moviepilot_cog")
        logger.info("Cog 卸载完成")
    except Exception as e:
        logger.error(f"Cog 卸载失败: {e}")

# Run bot
async def run_bot():
    if tokenes.is_bot_running:
        try:
            await load_extensions()
        except Exception as e:
            logger.error(f"Discord bot 已启动")
    else:
        try:
            logger.info("Discord bot 启动中...")
            tokenes.is_bot_running = True
            await load_extensions()
            await client.start(tokenes.bot_token)
        except Exception as e:
            logger.error(f"Discord bot 启动失败: {e}")
            tokenes.is_bot_running = False

    
async def stop():
    logger.info(f"is bot running: {tokenes.is_bot_running}")
    if tokenes.is_bot_running == True:
        logger.info("Discord bot 停止中...")
        try:
            await unload_extensions()
            tokenes.is_bot_running = False
            # client.clear()
        except Exception as e:
            logger.error(f"Discord bot 停止失败: {e}")
    else:
        logger.info("Discord bot 未运行")
