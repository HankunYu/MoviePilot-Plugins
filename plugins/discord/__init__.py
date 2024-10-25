#import discord
from enum import Enum
import asyncio, threading

# MoviePilot library
from app.core.event import eventmanager, Event
from app.log import logger
from app.plugins import _PluginBase
from app.core.event import eventmanager
from app.schemas.types import EventType, NotificationType
from typing import Any, List, Dict, Tuple
from app.utils.http import RequestUtils

try:
    import plugins.discord.discord_bot as discord_bot
    import plugins.discord.tokenes as tokenes
    from plugins.discord.cogs.moviepilot_cog import MPCog
except ImportError as e:
    logger.error(f"ImportError: {e}")
    

class Discord(_PluginBase):
    # 插件名称
    plugin_name = "discord"
    # 插件描述
    plugin_desc = "Discord 消息推送"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/HankunYu/MoviePilot-Plugins/main/icons/discord.png"
    # 主题色
    plugin_color = "#3B5E8E"
    # 插件版本
    plugin_version = "1.5.6"
    # 插件作者
    plugin_author = "hankun"
    # 作者主页
    author_url = "https://github.com/hankunyu"
    # 插件配置项ID前缀
    plugin_config_prefix = "discord_"
    # 加载顺序
    plugin_order = 1
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _webhook_url = None
    _enabled = False
    _debug_enabled = False

    # 消息类型
    _bot_token: str = None
    _gpt_token: str = None
    _all_types: List[NotificationType] = [
        NotificationType.Download, NotificationType.Subscribe, NotificationType.Organize, NotificationType.SiteMessage, 
        NotificationType.MediaServer, NotificationType.Manual
    ]
    _select_types: List[NotificationType] = []

    bot_thread = None
    loop = None

    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled")
            self._webhook_url = config.get("webhook_url")
            self._debug_enabled = config.get("debug_enabled")
            self._bot_token = config.get("bot_token")
            self._gpt_token = config.get("gpt_token")
            self._select_types = config.get("select_types")
            
            tokenes.bot_token = self._bot_token
            tokenes.gpt_token = self._gpt_token
            
            # 启动discord bot
            if(self._enabled and self._bot_token):
                if not self.bot_thread:
                    self.loop = asyncio.new_event_loop()
                    self.loop.create_task(discord_bot.run_bot())
                    self.bot_thread = threading.Thread(target=self.run_bot_thread, args=(self.loop,))
                    self.bot_thread.start()
                else:
                    future = asyncio.run_coroutine_threadsafe(discord_bot.run_bot(), self.loop)
                    logger.info(f"{future.result()}")
            else:
                # 如果插件被禁用，停止discord bot
                logger.info(f"is bot running: {tokenes.is_bot_running}")
                if(tokenes.is_bot_running and self._enabled == False and tokenes.is_bot_running == True):
                    asyncio.run(discord_bot.stop())
                
        logger.info(f"Discord插件初始化完成 version: {self.plugin_version}")

    def run_bot_thread(self,loop):
        loop.run_forever()

    def get_state(self) -> bool:
        return self._enabled
    
    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass
    
    # 插件配置页面
    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面，需要返回两块数据：1、页面配置；2、数据结构
        """
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'enabled',
                                            'label': '启用插件',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'debug_enabled',
                                            'label': 'debug模式',
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'webhook_url',
                                            'label': 'Discord webhook URL'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'content': [
                                    {
                                        'component': 'VTextField',
                                         'props': {
                                            'model': 'bot_token',
                                            'label': 'Discord bot token（可选)'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'content': [
                                    {
                                        'component': 'VTextField',
                                         'props': {
                                            'model': 'gpt_token',
                                            'label': 'OpenAI token（可选)'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'content': [
                                    {
                                        'component': 'VSelect',
                                        'props': {
                                            'chips': True,
                                            'multiple': True,
                                            'model': 'select_types',
                                            'label': '选择通知类型',
                                            'items': self._all_types
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                ]
            }
        ], {
            "enabled": False,
            "debug_enabled": False,
            "webhook_url": "",
            "bot_token": "",
            "gpt_token": "",
            "select_types": []
        }

    def get_page(self) -> List[dict]:
        pass

    
    @eventmanager.register(EventType.NoticeMessage)
    def send(self, event: Event):
        """
        向discord Webhook发送请求
        """
        if not self._enabled or not self._webhook_url or self._select_types is None or len(self._select_types) == 0:
            return
        
        # 提取消息内容
        msg_body = event.event_data
        text = msg_body.get("text")
        msg_type: NotificationType = msg_body.get("mtype")
        # 兼容v1
        if(msg_type == None):
            msg_type = msg_body.get("type")
        channel = msg_body.get("channel")
        title = msg_body.get("title")
        image = msg_body.get("image")
        link = msg_body.get("link")
        # 排除不响应的事件
        logger.info(f"msg_type: {msg_type.value}")
        logger.info(msg_body)
        logger.info(text)
        logger.info(title)
        logger.info(self._select_types)
        if msg_type.value not in self._select_types:
            logger.info(f"未选择发送的通知类型，跳过：{msg_type}")
            return
        
        # format data for discord
        def convert_data_to_embed():
            converted_text = ''
            fields = []
            
            # 处理站点事件
            if(msg_type == NotificationType.SiteMessage):
                if title == '站点数据统计':
                    lines = text.split('\n')
                    converted_text = '  '
                    for i in range(0, len(lines), 4):
                        # 提取站点和上传下载量
                        site = lines[i][1:].strip('】')
                        upload = lines[i + 1].split('：')[1]
                        download = lines[i + 2].split('：')[1]
                        if(site == '汇总'):
                            converted_text = f'**汇总**\n上传量:`{upload}`\n下载量:`{download}`'
                            continue
                        # 创建一个字典表示一个field
                        field = {
                            "name": "**"+site+"**",
                            "value": f"上传量:`{upload}`\n下载量:`{download}`",
                            "inline": True
                        }
                        # 将field添加到fields列表中
                        fields.append(field)

                elif title == '【站点自动登录】' or title == '【站点自动签到】':
                    lines = text.split('\n')
                    converted_text = '  '
                    # 提取总共登陆数据
                    for i in range(3):
                        field = {
                            "name": lines[i].split(':')[0],
                            "value": lines[i].split(':')[1],
                            "inline": True
                        }
                        fields.append(field)
                    # 去除前三行
                    lines = lines[3:]
                    for line in lines:
                        field = {
                        "name": line.split('】')[0] + '】',
                        "value": line.split('】')[1],
                        "inline": True
                        }
                        fields.append(field)

                elif title == "【自动删种任务完成】":
                    lines = text.split('\n')
                    # 提取总共处理种子数
                    converted_text = "**" + lines[0].split(' ')[0] + "** " + lines[0].split(' ')[1]
                    # 去除前一行
                    lines = lines[1:]
                    for line in lines:
                        parts = line.split(" ")
                        # 提取种子名称
                        name = " ".join(parts[:-2])
                        size = parts[-1]
                        field = {
                        "name": name,
                        "value": size,
                        "inline": True
                        }
                        fields.append(field)

            # 处理开始下载事件
            elif(msg_type == NotificationType.Download):
                lines =  text.split('\n')
                converted_text = '  '
                # 遍历每行内容
                for line in lines:
                    # 将每行内容按冒号分割为字段名称和值
                    if '：' not in line:
                        continue
                    name, value = line.split('：', 1)
                    
                    # 创建一个字典表示一个 field
                    if(name == '种子'):
                        continue
                    field = {
                        "name": name.strip(),
                        "value": value.strip(),
                        "inline": True
                    }
                    
                    # 将 field 添加到 fields 列表中
                    fields.append(field)
        
            # 处理其他事件
            else:
                lines =  text.split('，')
                converted_text = '  '
                # 遍历每行内容
                for line in lines:
                    # 将每行内容按冒号分割为字段名称和值
                    if '：' not in line:
                        converted_text = line
                    else: 
                        name, value = line.split('：', 1)
                    
                        # 创建一个字典表示一个 field
                        field = {
                            "name": name.strip(),
                            "value": value.strip(),
                            "inline": True
                        }
                        
                        # 将 field 添加到 fields 列表中
                        fields.append(field)

            
            # 构造 Webhook 请求的 JSON 数据
            data_json = {
                "embeds": [
                    {
                        "author": {
                            "name": "Movie Pilot",
                            "url": link if link else "https://github.com/jxxghp/MoviePilot",
                            "icon_url": "https://raw.githubusercontent.com/HankunYu/MoviePilot-Plugins-discord/main/icons/logo.jpg"
                        },
                        "title": title,
                        "url": link if link else "https://github.com/jxxghp/MoviePilot",
                        "color": 15258703,
                        "description": converted_text if converted_text else text,
                        "fields": fields,
                        "image": {
                            "url": "http://none.png" if image is None else image
                        }
                    }
                ]
                
            }

            return data_json
        

        if(self._debug_enabled):
            logger.info(f"event type: " + str(msg_type))
            logger.info(f"raw data: " + str(msg_body))
        
        
        # 转换数据为embed格式
        embed = convert_data_to_embed()
        if(self._debug_enabled):
            logger.info(f"title: " + title)
            logger.info(f"embed: " + str(embed))

        # 发送请求 
        ret = RequestUtils(content_type="application/json").post_res(self._webhook_url, json=embed)
        
        if ret:
            logger.info("发送成功")
        elif ret is not None:
            logger.error(f"发送失败，状态码：{ret.status_code}，返回信息：{ret.text} {ret.reason}")
        else:
            logger.error("发送失败，未获取到返回信息")

    def stop_service(self):
        """
        退出插件
        """
        if(self.bot_thread):
            logger.info(f"is bot running: {tokenes.is_bot_running}")
            future = asyncio.run_coroutine_threadsafe(discord_bot.stop(), self.loop)
            logger.info(f"{future.result()}")
            # self.loop.stop()
            # self.bot_thread = None
        pass
