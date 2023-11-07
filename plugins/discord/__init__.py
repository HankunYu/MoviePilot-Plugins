import discord
import requests

# MoviePilot library
from app.log import logger
from app.plugins import _PluginBase
from app.core.event import eventmanager
from app.schemas.types import EventType
from typing import Any, List, Dict, Tuple

class Discord(_PluginBase):
    # 插件名称
    plugin_name = "discord"
    # 插件描述
    plugin_desc = "Discord 消息推送"
    # 插件图标
    plugin_icon = "discord.png"
    # 主题色
    plugin_color = "#5A65EA"
    # 插件版本
    plugin_version = "1.0"
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
    _discord_token = None
    _enabled = False

    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled")
            self._discord_token = config.get("_discord_token")

    def get_state(self) -> bool:
        return self._enabled
    
    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass

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
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 8
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'discord_token',
                                            'label': 'Discord bot token'
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
            "discord_token": ""
        }

    def get_page(self) -> List[dict]:
        pass
