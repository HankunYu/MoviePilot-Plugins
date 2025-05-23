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
from app.core.config import settings
    

class Test(_PluginBase):
    # 插件名称
    plugin_name = "test"
    # 插件描述
    plugin_desc = "Test plugin"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/HankunYu/MoviePilot-Plugins/main/icons/discord.png"
    # 主题色
    plugin_color = "#3B5E8E"
    # 插件版本
    plugin_version = "1.3.9"
    # 插件作者
    plugin_author = "hankun"
    # 作者主页
    author_url = "https://github.com/hankunyu"
    # 插件配置项ID前缀
    plugin_config_prefix = "test_"
    # 加载顺序
    plugin_order = 1
    # 可使用的用户级别
    auth_level = 1


    _enabled = False
    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled")
            

    def get_state(self) -> bool:
        return self._enabled
    
    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        """
        获取插件API
        [{
            "path": "/xx",
            "endpoint": self.xxx,
            "methods": ["GET", "POST"],
            "summary": "API说明"
        }]
        """
        return [{
            "path": "/test_button_click",
            "endpoint": self.test_button_click,
            "methods": ["GET"],
            "summary": "测试按钮点击",
            "description": "测试按钮点击事件"
        }]
    
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
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False
        }

    def test_button_click(self):
        """
        测试按钮点击事件
        """
        logger.info("测试按钮被点击了！")

    def get_page(self) -> List[dict]:
        """
        获取插件页面
        """
        return [{
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
                                    'component': 'VBtn',
                                    'props': {
                                        'variant': 'tonal',
                                        'text': '测试按钮'
                                    },
                                    'events': {
                                        'click': {
                                            'api': 'plugin/test/test_button_click',
                                            'method': 'get',
                                            'params': {
                                                'apikey': settings.API_TOKEN
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }]
      

    def stop_service(self):
        """
        退出插件
        """
        pass
