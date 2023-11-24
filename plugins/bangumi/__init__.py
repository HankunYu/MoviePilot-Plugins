from app.log import logger
from app.plugins import _PluginBase
from app.core.event import eventmanager
from app.schemas.types import EventType
from typing import Any, List, Dict, Tuple

from app.db.models.mediaserver import MediaServerItem
from app.db import db_query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.db import Engine, DbOper, ScopedSession
from app.db.mediaserver_oper import MediaServerOper

import requests
import time
from urllib.parse import quote
import re

class Bangumi(_PluginBase):
    # 插件名称
    plugin_name = "Bangumi"
    # 插件描述
    plugin_desc = "动漫资源引用Bangumi评分，同步订阅/库存番剧到Bangumi"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/HankunYu/MoviePilot-Plugins/main/icons/bangumi.jpg"
    # 主题色
    plugin_color = "#5378A4"
    # 插件版本
    plugin_version = "0.14"
    # 插件作者
    plugin_author = "hankun"
    # 作者主页
    author_url = "https://github.com/hankunyu"
    # 插件配置项ID前缀
    plugin_config_prefix = "bangumi_"
    # 加载顺序
    plugin_order = 1
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _servers = ["plex", "jellyfin", "emby"]
    _enabled = False
    _token = ""
    _select_servers = None
    _db = None
    _media_in_library = None
    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled")
            self._token = config.get("token")
            self._select_servers = config.get("select_servers")
        if self._enabled:
            logger.debug("初始化Bangumi插件")
            self.get_media_in_library()


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
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'token',
                                            'label': 'Bangumi API Token',
                                            'rows': 1,
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'content': [
                                    {
                                        'component': 'VSelect',
                                        'props': {
                                            'chips': True,
                                            'multiple': True,
                                            'model': 'select_servers',
                                            'label': '选择同步用的媒体库',
                                            'items': self._servers
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
                                },
                                'content': [
                                    {
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'info',
                                            'variant': 'flat',
                                            'text': '请到 https://next.bgm.tv/demo/access-token 申请 API Token',
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False,
            "token": "",
            "select_servers": []
        }

    def get_page(self) -> List[dict]:
        pass

    def get_media_in_library(self):
        """
        获取库存中的媒体
        """
        db = ScopedSession

        results = db.query(MediaServerItem).filter(
            MediaServerItem.server.in_(self._select_servers)
        ).all()

        logger.info(f"找到媒体总共 {len(results)} 条")
        

    # 获取名字对应的条目ID
    def search_subject(self, name: str):
        # 去除特殊字符
        name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
        name = re.sub(r'\s+', ' ', name)
        # 转义
        keyword = quote(name)
        url = f"https://api.bgm.tv/search/subject/{keyword}?type=2&responseGroup=small"
        headers = {
            "accept: application/json"
        }
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            if res.json().get("results") == 0 or res.json().get("list").get("0").get("name_cn") != name or res.json().get("list").get("0").get("name") != name:
                return None
            return res.json().get("list").get("0").get("id")
        else:
            return None
    
    # 获取条目评分
    def get_rank(self, subject_id: str):
        url = f"https://api.bgm.tv/subject/{subject_id}"
        headers = {
            "accept: application/json"
        }
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.json().get("rating").get("score")
        else:
            return None
    
    # 添加收藏
    def add_collections(self, subject_id: str):
        url = f"https:://api.bgm.tv/v0/users/-/collections/{subject_id}"
        headers = {
            "accept: */*",
            "Authorization: Bearer {self._token}",
            "Content-Type: application/json"
        }
        data = {
            "type": 2,
            "rate": 0,
            "comment": "",
            "private": False,
            "tags": [""]
        }

        res = requests.post(url, headers=headers, data=data)
        if res.status_code == 204 or res.status_code == 202:
            return True
        else:
            return False
    
    @eventmanager.register(EventType.TransferComplete)
    def rmcdata(self, event):
        
        if not self._enabled:
            return

        def __to_dict(_event):
            """
            递归将对象转换为字典
            """
            if isinstance(_event, dict):
                for k, v in _event.items():
                    _event[k] = __to_dict(v)
                return _event
            elif isinstance(_event, list):
                for i in range(len(_event)):
                    _event[i] = __to_dict(_event[i])
                return _event
            elif isinstance(_event, tuple):
                return tuple(__to_dict(list(_event)))
            elif isinstance(_event, set):
                return set(__to_dict(list(_event)))
            elif hasattr(_event, 'to_dict'):
                return __to_dict(_event.to_dict())
            elif hasattr(_event, '__dict__'):
                return __to_dict(_event.__dict__)
            elif isinstance(_event, (int, float, str, bool, type(None))):
                return _event
            else:
                return str(_event)


        raw_data = __to_dict(event.event_data)
        targets_file = raw_data.get("transferinfo").get("file_list_new")



        

    def stop_service(self):
        """
        退出插件
        """
        pass

