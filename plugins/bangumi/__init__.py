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

import threading
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
    plugin_version = "0.20"
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
    _run_once = False
    _is_runing_sync = False
    _bangumi_id = ""
    _media_in_library = []
    _max_thread = 5
    _user_agent = "hankunyu/moviepilot_plugin (https://github.com/HankunYu/MoviePilot-Plugins)"
    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled")
            self._run_once = config.get("run_once")
            self._token = config.get("token")
            self._select_servers = config.get("select_servers")
        if self._enabled:
            logger.debug("初始化Bangumi插件")
            self.login()
            self._media_in_library = self.get_data("synced_media")
            if self._run_once and not self._is_runing_sync:
                self._is_runing_sync = True
                thread = threading.Thread(target=self.check_all_librarys)
                thread.start()
                self.update_config({
                    "enabled": self._enabled,
                    "run_once": False,
                    "token": self._token,
                    "select_servers": self._select_servers
                    })




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
                                            'model': 'run_once',
                                            'label': '同步一次媒体库到Bangumi',
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
            "run_once": False,
            "token": "",
            "select_servers": []
        }

    def get_page(self) -> List[dict]:
        pass

    # 检查媒体库中所有媒体，并尝试同步到Bangumi
    def check_all_librarys(self):
        results = self.get_media_in_library()
        if len(results) == 0:
            logger.info("媒体库中没有找到媒体，跳过同步全部媒体库")
            return
        logger.info("开始同步媒体库")
        # 第一次运行时初始化列表
        if self._media_in_library == None: self._media_in_library = []
        thread = []
        for media in results:
            if media.title in self._media_in_library: continue
            t = threading.Thread(target=self.sync_media, args=(media,))
            thread.append(t)
        for i in range(0, len(thread), self._max_thread):
            for j in range(i, min(i + self._max_thread, len(thread))):
                thread[j].start()
            for j in range(i, min(i + self._max_thread, len(thread))):
                thread[j].join()
        self.save_data("synced_media", self._media_in_library)
        self._is_runing_sync = False
        logger.info("媒体库同步完成")

    def login(self):
        if self._token == "":
            logger.info("未配置Bangumi API Token，跳过登录")
            return
        url = "https://api.bgm.tv/v0/me"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self._token}",
            "User-Agent": self._user_agent
        }
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            self._bangumi_id = res.json().get("id")
            logger.info("登录Bangumi成功")
        else:
            logger.info("登录Bangumi失败, 请检查API Token是否正确")
        
    # 同步媒体库
    def sync_media(self, media):
        subject_id = self.search_subject(media.title)
        self._media_in_library.append(media.title)
        if subject_id == None:
            subject_id = self.search_subject(media.original_title)
        if subject_id == None:
            logger.info(f"未在Bangumi中找到{media.title}的条目")
            return
        # 检查是否已收藏
        if self.check_subject_in_collections(subject_id):
            logger.info(f"{media.title}已收藏，跳过")
            return
        # 添加收藏
        if self.add_collections(subject_id):
            logger.info(f"{media.title}收藏成功")
        
    
    # 获取媒体库中的媒体
    def get_media_in_library(self):
        db = ScopedSession

        results = db.query(MediaServerItem).filter(
            MediaServerItem.server.in_(self._select_servers)
        ).all()

        db.close()
        return results
        

    # 获取名字对应的条目ID
    def search_subject(self, name: str):
        # 去除特殊字符
        name = re.sub(r'[\W_]+', '',name)
        # 转义
        keyword = quote(name)
        url = f"https://api.bgm.tv/search/subject/{keyword}?type=2&responseGroup=small"
        headers = {
            "accept": "application/json",
            "User-Agent": self._user_agent
        }
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            if res.json().get("results") == 0:
                return None
            results = res.json().get("list")
            for result in results:
                result_name = re.sub(r'[\W_]+', '',result.get("name"))
                result_name_cn = re.sub(r'[\W_]+', '',result.get("name_cn"))
                if result_name == name or result_name_cn == name:
                    return result.get("id")
                else:
                    # 尝试移除罗马字符
                    pattern = re.compile(r'[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩIVX]')
                    result_name = re.sub(pattern, '',result_name)
                    result_name_cn = re.sub(pattern, '',result_name_cn)
                    name = re.sub(pattern, '',name)
                    if result_name == name or result_name_cn == name:
                        return result.get("id")
        else:
            return None
    
    # 获取条目评分
    def get_rank(self, subject_id: str):
        url = f"https://api.bgm.tv/subject/{subject_id}"
        headers = {
            "accept": "application/json",
            "User-Agent": self._user_agent
        }
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.json().get("rating").get("score")
        else:
            return None
    
    # 检查是否已收藏
    def check_subject_in_collections(self, subject_id: str):
        url = f"https://api.bgm.tv/v0/users/{self._bangumi_id}/collections/{subject_id}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self._token}",
            "User-Agent": self._user_agent
        }
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return True
        else:
            return False

    # 添加收藏
    def add_collections(self, subject_id: str):
        url = f"https:://api.bgm.tv/v0/users/-/collections/{subject_id}"
        headers = {
            "accept": "*/*",
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "User-Agent": self._user_agent
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

