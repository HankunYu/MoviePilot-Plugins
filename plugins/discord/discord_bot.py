import discord, discord.webhook, asyncio, os
from discord.ext import commands
import plugins.discord.tokenes as tokenes
import plugins.discord.cogs.moviepilot_cog as moviepilot_cog
from app.log import logger

is_running = False
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
    global is_running
    logger.info("Discord bot 启动中...")
    async with client:
        await load_extensions()
        
        if is_running:
            logger.info("Discord bot 已启动")
        else:
            try:
                await client.start(tokenes.bot_token)
                is_running = True
            except Exception as e:
                logger.error(f"Discord bot 启动失败: {e}")

    
async def stop():
    logger.info("Discord bot 停止中...")
    await unload_extensions()