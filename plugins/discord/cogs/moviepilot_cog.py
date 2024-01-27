import discord, sys, re
from typing import Optional, List, Tuple
from discord import app_commands
from discord.ext import commands
from app.log import logger
from app.chain.download import DownloadChain
from app.chain.search import SearchChain
from app.chain.subscribe import SubscribeChain
from app.core.context import MediaInfo, TorrentInfo, Context
from app.core.metainfo import MetaInfo
from plugins.discord.gpt import GPT
import plugins.discord.tokenes as tokenes

class MPCog(commands.Cog):
    on_conversion = False
    current_channel = None
    downloadchain = None
    searchchain = None
    subscribechain = None
    gpt = None

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.downloadchain = DownloadChain()
        self.searchchain = SearchChain()
        self.subscribechain = SubscribeChain()
        self.gpt = GPT(token=tokenes.gpt_token)

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
            reply = self.gpt.generate_reply(msg)
            if reply != None:
                await message.channel.send(reply)
            else:
                await message.channel.send("啊好像哪里出错了...这不应该，你再试试？不行就算了。")
            game = discord.Game("模仿明日香中...")
            await self.bot.change_presence(status=discord.Status.online, activity=game)

    # slash command
    @app_commands.command(description="停止GPT对话")
    async def stop(self, interaction: discord.Interaction):
        game = discord.Game("看电影中...")
        self.on_conversion = False
        await self.bot.change_presence(status=discord.Status.idle, activity=game)
        await interaction.response.send_message("^^")

    @app_commands.command(description="清除对话记录")
    async def clear(self, interaction: discord.Interaction):
        self.gpt.clear_chat_history()
        await interaction.response.send_message("对话记录已经清除")

    @app_commands.command(description="下载电影，如果找到多个结果，返回结果列表，让用户选择下载")
    async def download(self, interaction: discord.Interaction, title: str):
        await interaction.response.send_message("正在下载电影 " + title)

        # 搜索
        meta = MetaInfo(title=title)
        medias: Optional[List[MediaInfo]] = self.searchchain.search_medias(meta=meta)
        if not medias:
            await interaction.followup.send("无法识别到媒体信息 " + title)
            return
        # 如果找到多个结果，返回结果列表，让用户选择下载
        if len(medias) > 0:
            for media in medias:
                fields = []
                media_title = {
                    "name": "标题",
                    "value": media.title
                }
                release_date = {
                    "name": "发布日期",
                    "value": media.release_date
                }
                vote_average = {
                    "name": "评分",
                    "value": media.vote_average
                }
                fields.append(media_title)
                fields.append(release_date)
                fields.append(vote_average)
                embed = discord.Embed(title=media.title,
                                      description=media.tmdb_info["overview"],
                                      url=media.homepage)
                for field in fields:
                    embed.add_field(name=field["name"], value=field["value"], inline=True)
                if media.backdrop_path:
                    embed.set_image(url=media.backdrop_path)
                # 组合上下文
                context = Context(media_info=media, meta_info=meta)
                view = DownloadView(context)
                await interaction.followup.send(embed=embed, view=view)
                
                
        # 如果只找到一个结果，直接下载
        else:
            mediainfo = medias[0]
            exist_flag, no_exists = self.downloadchain.get_no_exists_info(meta=meta, mediainfo=mediainfo)
            if exist_flag:
                await interaction.followup.send(f'{mediainfo.title_year} 已存在')
                return
            contexts = self.searchchain.process(mediainfo = mediainfo, no_exists=no_exists)
            if len(contexts) == 0:
                await interaction.followup.send("没有找到资源 " + title)
            # 自动下载
            downloads, lefts = self.downloadchain.batch_download(contexts=contexts, no_exists=no_exists,
                                                                                    username="Discord Bot")
            if downloads and not lefts:
                await interaction.followup.send(f'{mediainfo.title_year} 添加下载')
            else:
                await interaction.followup.send(f'{mediainfo.title_year} 下载未完整，开始订阅')
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
        medias: Optional[List[MediaInfo]] = self.searchchain.search_medias(meta=meta)
        if not medias:
            await interaction.followup.send("无法识别到媒体信息 " + title)
            return
        # 如果找到多个结果，返回结果列表，让用户选择下载
        if len(medias) > 0:
            for media in medias:
                fields = []
                media_title = {
                    "name": "标题",
                    "value": media.title
                }
                release_date = {
                    "name": "发布日期",
                    "value": media.release_date
                }
                vote_average = {
                    "name": "评分",
                    "value": media.vote_average
                }
                fields.append(media_title)
                fields.append(release_date)
                fields.append(vote_average)
                embed = discord.Embed(title=media.title,
                                      description=media.tmdb_info["overview"],
                                      url=media.homepage)
                for field in fields:
                    embed.add_field(name=field["name"], value=field["value"], inline=True)
                if media.backdrop_path:
                    embed.set_image(url=media.backdrop_path)
                # 组合上下文
                context = Context(media_info=media, meta_info=meta)
                view = SubscribeChain(context)
                await interaction.followup.send(embed=embed, view=view)
                
                
        # 如果只找到一个结果，直接订阅
        else:
            mediainfo = medias[0]
            await interaction.followup.send(f'{mediainfo.title_year} 添加订阅')
            self.subscribechain.add(title=mediainfo.title,
                                                        year=mediainfo.year,
                                                        mtype=mediainfo.type,
                                                        tmdbid=mediainfo.tmdb_id,
                                                        season=meta.begin_season,
                                                        exist_ok=True,
                                                        username="Discord Bot")


    @app_commands.command(description="搜索种子，选择下载")
    async def search(self, interaction: discord.Interaction, title: str):
        await interaction.response.send_message("正在搜索电影 " + title)
        game = discord.Game("搜索电影中...")
        await self.bot.change_presence(status=discord.Status.online, activity=game)
        # 搜索
        meta = MetaInfo(title=title)
        mediainfo = self.searchchain.recognize_media(meta=meta)
        if not mediainfo:
            await interaction.followup.send("无法识别到媒体信息 " + title)
            return
        exist_flag, no_exists = self.downloadchain.get_no_exists_info(meta=meta, mediainfo=mediainfo)
        if exist_flag:
            await interaction.followup.send(f'{mediainfo.title_year} 已存在')
            return
        
        contexts = self.searchchain.process(mediainfo = mediainfo, no_exists=no_exists)
        if len(contexts) == 0:
            await interaction.followup.send("没有找到资源 " + title)
            game = discord.Game("看电影中...")
            await self.bot.change_presence(status=discord.Status.idle, activity=game)
        else:
            for context in contexts:
                torrent = context.torrent_info
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
                    "value": str(round(torrent.size / 1024 / 1024 / 1024, 2)) + " GB"
                }
                seeders = {
                    "name": "做种数",
                    "value": torrent.seeders
                }
                peers = {
                    "name": "下载数",
                    "value": torrent.peers
                }
                release_date = {
                    "name": "发布日期",
                    "value": torrent.pubdate
                }
                free = {
                    "name": "促销",
                    "value": torrent.volume_factor
                }
                fields.append(site_name)
                fields.append(torrent_size)
                fields.append(release_date)
                fields.append(seeders)
                fields.append(peers)
                fields.append(free)

                for field in fields:
                    embed.add_field(name=field["name"], value=field["value"], inline=True)
                
                view = DownloadView(context)
                await interaction.followup.send(embed=embed, view=view)
                
            game = discord.Game("看电影中...")
            await self.bot.change_presence(status=discord.Status.idle, activity=game)

class DownloadView(discord.ui.View):
    context = None
    downloadchain = None
    subscribechain = None
    def __init__(self, context: Context):
        super().__init__(timeout=180)
        self.context = context
        self.subscribechain = SubscribeChain()
        self.downloadchain = DownloadChain()

    @discord.ui.button(label="下载", style = discord.ButtonStyle.blurple)
    async def download(self, button: discord.ui.Button, interaction: discord.Interaction):
        # 如果已经有种子信息，直接下载
        if(self.context.torrent_info != None):
            self.downloadchain.download_single(self.context)
            await interaction.response.send_message(f"添加下载任务 {self.context.torrent_info.title} 成功")
        # 如果没有种子信息，先搜索种子，再下载
        else:
            mediainfo = self.context.media_info
            meta = self.context.meta_info
            exist_flag, no_exists = self.downloadchain.get_no_exists_info(meta=meta, mediainfo=mediainfo)
            if exist_flag:
                await interaction.response.send(f'{mediainfo.title_year} 已存在')
                return
            contexts = self.searchchain.process(mediainfo = mediainfo, no_exists=no_exists)
            if len(contexts) == 0:
                await interaction.response.send("没有找到资源 " + mediainfo.title_year)
                return
            # 自动下载
            downloads, lefts = self.downloadchain.batch_download(contexts=contexts, no_exists=no_exists,
                                                                                    username="Discord Bot")
            if downloads and not lefts:
                await interaction.response.send(f'{mediainfo.title_year} 添加下载')
            else:
                await interaction.response.send(f'{mediainfo.title_year} 下载未完整，开始订阅')
                self.subscribechain.add(title=mediainfo.title,
                                                            year=mediainfo.year,
                                                            mtype=mediainfo.type,
                                                            tmdbid=mediainfo.tmdb_id,
                                                            season=meta.begin_season,
                                                            exist_ok=True,
                                                            username="Discord Bot")

class SubscribeView(discord.ui.View):
    context = None
    subscribechain = None
    def __init__(self, context: Context):
        super().__init__(timeout=180)
        self.context = context
        self.subscribechain = SubscribeChain()

    @discord.ui.button(label="订阅", style = discord.ButtonStyle.blurple)
    async def subscribe(self, button: discord.ui.Button, interaction: discord.Interaction):
        mediainfo = self.context.media_info
        meta = self.context.meta_info
        self.subscribechain.add(title=mediainfo.title,
                                year=mediainfo.year,
                                mtype=mediainfo.type,
                                tmdbid=mediainfo.tmdb_id,
                                season=meta.begin_season,
                                exist_ok=True,
                                username="Discord Bot")
        await interaction.response.send_message(f"已添加订阅 {mediainfo.title_year}")
async def setup(bot : commands.Bot):
    await bot.add_cog(MPCog(bot))