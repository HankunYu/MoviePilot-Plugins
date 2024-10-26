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
    plugin_version = "1"
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
            
            # 启动discord bot
            if(self._enabled):
                logger.info(f"Discord插件初始化完成 version: {self.plugin_version}")

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
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False
        }

    def get_page(self) -> List[dict]:
        pass

    
    @eventmanager.register(EventType.NoticeMessage)
    def send(self, event: Event):
        msg_body = event.event_data
        text = msg_body.get("text")
        msg_type: NotificationType = msg_body.get("mtype")
        logger.info(f"event type: " + str(msg_type))
        return
      

    def stop_service(self):
        """
        退出插件
        """
        pass
