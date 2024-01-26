import discord, sys, re
from discord import app_commands
from discord.ext import commands
from app.log import logger
from app.chain.download import DownloadChain
from app.chain.search import SearchChain
from app.chain.subscribe import SubscribeChain
from app.core.context import MediaInfo, TorrentInfo, Context
from app.core.metainfo import MetaInfo
import plugins.discord.gpt as gpt

class MPCog(commands.Cog):
    on_conversion = False
    current_channel = None
    downloadchain = None
    searchchain = None
    subscribechain = None

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.downloadchain = DownloadChain()
        self.searchchain = SearchChain()
        self.subscribechain = SubscribeChain()

    # 监听ready事件，bot准备好后打印登录信息
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f'bot 登录成功 - {self.bot.user}')
        game = discord.Game("看电影中...")
        await self.bot.change_presence(status=discord.Status.idle, activity=game)
        slash = await self.bot.tree.sync()
        logger.info(f"已载入 {len(slash)} 个指令")

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

        # 搜索
        meta = MetaInfo(title=title)
        mediainfo = self.searchchain.recognize_media(meta=meta)
        if not mediainfo:
            await interaction.followup.send_message("无法识别到媒体信息 " + title)
            return
        exist_flag, no_exists = self.downloadchain.get_no_exists_info(meta=meta, mediainfo=mediainfo)
        if exist_flag:
            await interaction.followup.send_message(f'{mediainfo.title_year} 已存在')
            return
        
        contexts = self.searchchain.process(mediainfo = mediainfo, no_exists=no_exists)
        if len(contexts) == 0:
            await interaction.followup.send_message("没有找到资源 " + title)
         # 自动下载
        downloads, lefts = self.downloadchain.batch_download(contexts=contexts, no_exists=no_exists,
                                                                                 username="Discord Bot")
        if downloads and not lefts:
            await interaction.followup.send_message(f'{mediainfo.title_year} 下载完成')
        else:
            await interaction.followup.send_message(f'{mediainfo.title_year} 下载未完整，开始订阅')
            self.subscribechain.add(title=mediainfo.title,
                                                        year=mediainfo.year,
                                                        mtype=mediainfo.type,
                                                        tmdbid=mediainfo.tmdb_id,
                                                        season=meta.begin_season,
                                                        exist_ok=True,
                                                        username="Discord Bot")
    
    @app_commands.command(description="订阅电影")
    async def subscribe(self, interaction: discord.Interaction, title: str):
        await interaction.response.send_message("正在订阅 " + title)
        # 搜索
        meta = MetaInfo(title=title)
        mediainfo = self.searchchain.recognize_media(meta=meta)
        if not mediainfo:
            await interaction.followup.send_message("无法识别到媒体信息 " + title)
            return
        exist_flag, no_exists = self.downloadchain.get_no_exists_info(meta=meta, mediainfo=mediainfo)
        if exist_flag:
            await interaction.followup.send_message(f'{mediainfo.title_year} 已存在')
            return

         # 订阅
        self.subscribechain.add(title=mediainfo.title,
                                                    year=mediainfo.year,
                                                    mtype=mediainfo.type,
                                                    tmdbid=mediainfo.tmdb_id,
                                                    season=meta.begin_season,
                                                    exist_ok=True,
                                                    username="Discord Bot")
        
        await interaction.followup.send_message(f'已订阅 {mediainfo.title_year}')


    @app_commands.command(description="搜索电影")
    async def search(self, interaction: discord.Interaction, title: str):
        await interaction.response.send_message("正在搜索电影 " + title)

        # 搜索
        meta = MetaInfo(title=title)
        mediainfo = self.searchchain.recognize_media(meta=meta)
        if not mediainfo:
            await interaction.followup.send_message("无法识别到媒体信息 " + title)
            return
        exist_flag, no_exists = self.downloadchain.get_no_exists_info(meta=meta, mediainfo=mediainfo)
        if exist_flag:
            await interaction.followup.send_message(f'{mediainfo.title_year} 已存在')
            return
        
        contexts = self.searchchain.process(mediainfo = mediainfo, no_exists=no_exists)
        if len(contexts) == 0:
            await interaction.followup.send_message("没有找到资源 " + title)
        else:
            for context in contexts:
                torrent = context.torrent
                embed = discord.Embed(title=torrent.title, 
                                      description=torrent.description,
                                      url=torrent.page_url)
                fields = []
                site_name = {
                    "name": "站点",
                    "value": torrent.site_name
                }
                torrent_size = {
                    "name": "种子大小",
                    "value": torrent.size
                }
                seeders = {
                    "name": "做种数",
                    "value": torrent.seeders
                }
                peers = {
                    "name": "下载数",
                    "value": torrent.peers
                }
                fields.append(site_name)
                fields.append(torrent_size)
                fields.append(seeders)
                fields.append(peers)

                for field in fields:
                    embed.add_field(name=field[0], value=field[1], inline=True)
                
                view = DownloadView(context, self.downloadchain)
                await interaction.followup.send_message(embed=embed, view=view)

class DownloadView(discord.ui.View):
    context = None
    def __init__(self, context: Context, downloadchain: DownloadChain):
        super().__init__(timeout=180)
        self.context = context

    @discord.ui.button(label="下载", style = discord.ButtonStyle.blurple)
    async def download(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.downloadchain.dowload_single(self.context)

class SubscribeView(discord.ui.View):
    context = None
    def __init__(self, context: Context, subscribechain: SubscribeChain):
        super().__init__(timeout=180)
        self.context = context

    @discord.ui.button(label="订阅", style = discord.ButtonStyle.blurple)
    async def subscribe(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.subscribechain.add(self.context, username = "Discord Bot")

async def setup(bot : commands.Bot):
    await bot.add_cog(MPCog(bot))