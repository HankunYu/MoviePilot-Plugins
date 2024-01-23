import discord, sys, re
from discord import app_commands
from discord.ext import commands
sys.path.append("..") 
import gpt

class MPCog(commands.Cog):
    on_conversion = False
    current_channel = None

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 监听ready事件，bot准备好后打印登录信息
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'bot 登录成功 - {self.bot.user}')
        game = discord.Game("看电影中...")
        await self.bot.change_presence(status=discord.Status.idle, activity=game)
        slash = await self.bot.tree.sync()
        print(f"已载入 {len(slash)} 个指令")

    # 监听mention事件，使用gpt生成回复
    @commands.Cog.listener()
    async def on_message(self,message):
        if message.author == self.bot.user:
            return

        if self.bot.user.mentioned_in(message) or self.on_conversion:
            msg  = re.sub(r'<.*?>', '', message.content)
            self.on_conversion = True
            self.current_channel = message.channel
            reply = gpt.generate_reply(msg)
            print('reply: ', reply)
            if reply != None:
                await message.channel.send(reply)
            else:
                await message.channel.send("啊好像哪里出错了...这不应该，你再试试？不行就算了。")
            game = discord.Game("模仿GPT-3.5中...")
            await self.bot.change_presence(status=discord.Status.online, activity=game)

    # slash command
    @app_commands.command(description="停止GPT对话")
    async def stop(self, interaction: discord.Interaction):
        game = discord.Game("看电影中...")
        self.on_conversion = False
        await self.bot.change_presence(status=discord.Status.idle, activity=game)
        await interaction.response.send_message("^^")

    @app_commands.command()
    async def clear(self, interaction: discord.Interaction):
        gpt.clear_chat_history()
        await interaction.response.send_message("对话记录已经清除")

    @app_commands.command(description="自动搜索并下载电影")
    async def download(self, interaction: discord.Interaction, title: str):
        await interaction.response.send_message("正在下载电影 " + title)

async def setup(bot : commands.Bot):
    await bot.add_cog(MPCog(bot))