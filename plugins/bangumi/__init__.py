import datetime
from app.log import logger
from app.plugins import _PluginBase
from app.core.event import eventmanager
from app.core.config import settings
from app.schemas.types import EventType
from typing import Optional, Any, List, Dict, Tuple

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.chain.download import DownloadChain
from app.chain.search import SearchChain
from app.chain.subscribe import SubscribeChain
from app.db.models.mediaserver import MediaServerItem
from app.db.models.subscribe import Subscribe
from app.db import db_query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.db import ScopedSession
from app.core.plugin import PluginManager

import threading
from threading import Thread
import requests
from urllib.parse import quote
import re
import os
import json
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
    plugin_version = "0.63"
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
    _enable_sync = False
    _sycn_subscribe_rank = False
    _update_nfo = False
    _update_nfo_all_once = False
    _library_path = ""
    _interval = "60"
    _clear_cache = False

    _is_runing_sync = False
    _is_runing_update_nfo = False
    _is_runing_update_rank = False
    _is_runing_cache = False
    _bangumi_id = ""
    _media_info = []
    _max_thread = 100
    _user_agent = "hankunyu/moviepilot_plugin (https://github.com/HankunYu/MoviePilot-Plugins)"
    _scheduler: Optional[BackgroundScheduler] = None

    mediainfo = {
        "title": None,
        "original_title": None,
        "subject_id": None,
        "rank": None,
        "status": None,
        "synced": False
    }
    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled")
            self._clear_cache = config.get("clear_cache")
            self._enable_sync = config.get("enable_sync")
            self._token = config.get("token")
            self._select_servers = config.get("select_servers")
            self._update_nfo = config.get("update_nfo")
            self._update_nfo_all_once = config.get("update_nfo_all_once")
            self._sycn_subscribe_rank = config.get("sync_subscribe_rank")
            self._library_path = config.get("library_path")
            self._interval = config.get("interval")
        
        # 清除缓存
        if self._clear_cache:
            self.clear_cache()
            self._clear_cache = False
            self.__update_config()
        if self._enabled:
            self.check_cache()
            self.login()
            logger.debug("初始化Bangumi插件")
            # self._scheduler = BackgroundScheduler(timezone=settings.TZ)
            # # 定时任务
            # if self._enable_sync and self._interval != "":
            #     try:
            #         try:
            #             interval = int(self._interval)
            #         except ValueError:
            #             logger.error("定时任务执行间隔必须为数字")
            #             interval = 60
            #         if interval <= 1:
            #             logger.error("定时任务执行间隔必须大于1")
            #             interval = 60
            #         self._scheduler.add_job(self.check_all_librarys_for_sync, "interval", minutes=interval, name="Bangumi同步媒体库到已看")
            #     except Exception as e:
            #         logger.error(f"添加定时任务 同步媒体库 失败: {e}")

            # 运行一次同步到Bangumi
            if self._enable_sync and not self._is_runing_sync:
                thread = threading.Thread(target=self.check_all_librarys_for_sync)
                thread.start()
            
            # 更新全部NFO文件
            if self._update_nfo_all_once and not self._is_runing_update_nfo:
                self._update_nfo_all_once = False
                self.__update_config()
                thread = threading.Thread(target=self.update_nfo_all_once)
                thread.start()
            # 更新订阅页面评分
            if self._sycn_subscribe_rank and not self._is_runing_update_rank:
                thread = threading.Thread(target=self.update_subscribe_rank)
                thread.start()

    def __update_config(self):
        self.update_config({
            "enabled": self._enabled,
            "clear_cache": self._clear_cache,
            "enable_sync": self._enable_sync,
            "token": self._token,
            "select_servers": self._select_servers,
            "update_nfo": self._update_nfo,
            "update_nfo_all_once": self._update_nfo_all_once,
            "sync_subscribe_rank": self._sycn_subscribe_rank,
            "library_path": self._library_path,
            "interval": self._interval
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
                                            'model': 'clear_cache',
                                            'label': '清除缓存',
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
                                            'model': 'enable_sync',
                                            'label': '同步媒体库到Bangumi为已看',
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
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'update_nfo',
                                            'label': '使用Bangumi评分更新新入库NFO文件',
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
                                            'model': 'update_nfo_all_once',
                                            'label': '使用Bangumi评分更新所有已入库NFO文件',
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
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'sync_subscribe_rank',
                                            'label': '使用Bangumi评分更新订阅页面评分',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'interval',
                                            'label': '定时任务执行间隔 (分钟)',
                                            'rows': 1,
                                            'value': '60'
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
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'library_path',
                                            'label': '动漫媒体库路径',
                                            'placeholder': '如果有剧场版就包括电影路径。一行一个路径。',
                                            'rows': 3,
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
                                            'text': '请到 https://next.bgm.tv/demo/access-token 申请 API Token\n第一次启用会扫描并缓存所有媒体库中的番剧，可能会花费较长时间，请耐心等待',
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
            "clear_cache": False,
            "enable_sync": False,
            "token": "",
            "select_servers": [],
            "update_nfo": False,
            "update_nfo_all_once": False,
            "sync_subscribe_rank": False,
            "library_path": "",
            "interval": "60"
        }

    def get_page(self) -> List[dict]:
        pass
    # 检查缓存
    def check_cache(self):
        self._media_info = self.get_data("mediainfo")
        # 如果没有缓存，初始化列表
        if self._media_info == None: 
            logger.info("没有找到缓存，初始化列表")
            self._media_info = []
            thread = threading.Thread(target=self.cache_library)
            thread.start()
    # 清除缓存
    def clear_cache(self):
        self._media_info = []
        self.save_data("mediainfo", self._media_info)
        logger.info("清除缓存完成")

    # 缓存媒体库数据 需要保证其他函数不会在更新缓存时调用缓存
    def cache_library(self):
        if self._is_runing_cache: return
        self._is_runing_cache = True
        logger.info("开始缓存媒体库数据")
        results = self.get_medias_in_library()
        if len(results) == 0:
            logger.error("媒体库中没有找到媒体，请检查是否设置正确")
            return
        for media in results:
            media_info = self.mediainfo
            try:
                season_list = json.loads(media.seasoninfo)
            except (AttributeError, KeyError, TypeError):
                season_list = []
            if len(season_list) > 0:
                # 添加每一季
                for season in season_list:
                    # 转为int
                    season_number = int(season)
                    # 第二季以上才需要加季数
                    if season_number > 1:
                        chinese_number = ["零","一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"]
                        chinese_season = " 第" + chinese_number[season_number] + "季"
                        media_info['title']= media.title + chinese_season
                    else:
                        media_info["title"] = media.title

                    media_info["original_title"] = media.original_title
                    # 如果已存在于缓存中，跳过
                    if media_info['title'] in [subject["title"] for subject in self._media_info]: continue
                    media_info = self.get_bangumi_info(media_info)
                    logger.info(f'运行到这里正常')
                    logger.info(f"添加 {media_info['title']} 到缓存中, 条目ID: {media_info['subject_id']}, 评分: {media_info['rank']}, 状态: {media_info['status']}")
                    self._media_info.append(media_info)
            else:
                # 如果已存在于缓存中，跳过
                if media.title in [subject["title"] for subject in self._media_info]: continue
                media_info["title"] = media.title
                media_info["original_title"] = media.original_title
                media_info = self.get_bangumi_info(media_info)
                logger.info(f"添加 {media_info['title']} 到缓存中, 条目ID: {media_info['subject_id']}, 评分: {media_info['rank']}, 状态: {media_info['status']}")
                self._media_info.append(media_info)
        # 保存缓存
        self.save_data("mediainfo", self._media_info)
        self._is_runing_cache = False
        logger.info("媒体库数据缓存完成")
        
    # 检查缓存中所有媒体，并尝试同步到Bangumi
    def check_all_librarys_for_sync(self):
        if self._is_runing_sync or self._is_runing_cache: return
        self._is_runing_sync = True
        # 更新缓存
        self.cache_library()
        if len(self._media_info) == 0:
            logger.info("媒体库中没有找到媒体，跳过同步全部媒体库")
            return
        logger.info("开始同步媒体库")
        for info in self._media_info:
            self.sync_media_to_bangumi(info)
        self._is_runing_sync = False
        logger.info("媒体库同步完成")

    # 获取用户UID
    def login(self):
        if self._token == "":
            logger.info("请配置Bangumi API Token")
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
    
    # 根据媒体数据获取Bangumi上数据
    def get_bangumi_info(self, info: mediainfo):
         # 新建媒体信息
        new_media_info = self.mediainfo
        new_media_info["title"] = info['title']
        new_media_info["original_title"] = info['original_title']
        new_media_info["subject_id"] = None
        new_media_info["rank"] = None
        new_media_info["status"] = None
        new_media_info["synced"] = False

        # 获取条目ID
        subject_id = self.search_subject(new_media_info["title"])
        # 如果没有找到条目ID，尝试使用原始名称
        if subject_id == None:
            subject_id = self.search_subject(new_media_info["original_title"])
        # 如果没有找到条目ID，跳过
        if subject_id == None:
            return new_media_info
        new_media_info["subject_id"] = subject_id
        # 获取评分
        new_media_info['rank'] = self.get_rank(subject_id)
        # 检查收藏状态
        status = self.get_collection_status(subject_id)
        new_media_info["status"] = status
        # copy是否已同步
        new_media_info["synced"] = info["synced"]

        return new_media_info

    # 同步番剧到 Bangumi 为已看
    def sync_media_to_bangumi(self, info: mediainfo):
        new_mediainfo = self.mediainfo
        # 如果已同步，跳过
        if new_mediainfo["synced"] == True: 
            logger.info(f"{new_mediainfo['title']}已同步，跳过")
            return
        # 如果已收藏，跳过
        if new_mediainfo['status'] != None:
            logger.info(f"{new_mediainfo['title']}已收藏，跳过")
            new_mediainfo["synced"] = True
            self.add_or_update_media_info(new_mediainfo)
            return
        # 添加收藏
        if self.add_collections(new_mediainfo["subject_id"]):
            new_mediainfo["synced"] = True
            new_mediainfo["status"] = 3
            self.add_or_update_media_info(new_mediainfo)
            logger.info(f"{new_mediainfo['title']}收藏成功")
        else:
            logger.info(f"{new_mediainfo['title']}收藏失败")
    
    # 获取媒体库中的媒体 目标为数据库中的 MediaServerItem 表
    def get_medias_in_library(self):
        db = ScopedSession

        results = db.query(MediaServerItem).filter(
            MediaServerItem.server.in_(self._select_servers)
        ).all()

        db.close()
        return results      

    # 获取名字对应的条目ID 将移除特殊字符后进行匹配
    def search_subject(self, name: str):
        if name == None: return None
        # 转义
        keyword = quote(name)
        url = f"https://api.bgm.tv/search/subject/{keyword}?type=2&responseGroup=small"
        headers = {
            "accept": "application/json",
            "User-Agent": self._user_agent
        }
        res = requests.get(url, headers=headers)

        # 检查返回类型
        content_type = res.headers.get('Content-Type')
        if 'application/json' not in content_type: return None

        if res.status_code == 200:
            if res.json().get("results") == 0:
                return None
            results = res.json().get("list")
            if results == None: return None
            for result in results:
                clear_name = re.sub(r'[\W_]+', '',name)
                result_name = re.sub(r'[\W_]+', '',result.get("name"))
                result_name_cn = re.sub(r'[\W_]+', '',result.get("name_cn"))
                if result_name == clear_name or result_name_cn == clear_name:
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

        content_type = res.headers.get('Content-Type')
        if 'application/json' not in content_type: return None

        if res.status_code == 200:
            try:
                rank = res.json().get("rating").get("score")
            except (AttributeError, KeyError, TypeError):
                return None
            return res.json().get("rating").get("score") == 0 and 0 or res.json().get("rating").get("score")
        else:
            return None
    
    # 检查 Bangumi 是否已收藏
    def check_subject_in_collections(self, subject_id: str):
        return self.get_collection_status(subject_id) is not None

    # 添加收藏
    def add_collections(self, subject_id: str):
        url = f"https://api.bgm.tv/v0/users/-/collections/{subject_id}"
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

        res = requests.post(url, headers=headers, json=data)
        if res.status_code == 204 or res.status_code == 202:
            return True
        else:
            return False
    
    # 更新NFO文件的评分
    def update_nfo(self, file_path: str, subject_id: str):
        # 获取评分
        rank = self.get_rank(subject_id)
        if rank == None: return False

        # 更新NFO
        if not os.path.exists(file_path):
            return False
        with open(file_path, 'r') as file:
            content = file.read()
        content = re.sub(r'<rating>.*?</rating>', f'<rating>{rank}</rating>', content)
        if re.search(r'<rating>.*?</rating>', content) == None:
            logger.info(f"{file_path} 中没有rating字段")
            return False
        with open(file_path, 'w') as file:
            file.write(content)
            logger.info(f"更新{file_path}的评分为{rank}")
            return True
    
    # 更新所有已入库的NFO文件
    def update_nfo_all_once(self):
        if self._is_runing_update_nfo: 
            logger.info("已有更新NFO文件的任务正在运行")
            return
        if self._is_runing_cache:
            logger.info("正在运行缓存媒体库数据任务，请稍后再试")
            return
        logger.info("开始更新已入库的NFO文件")
        self._is_runing_update_nfo = True
        threads = []
        paths = []
        for path in self._library_path.split('\n'):
            if os.path.exists(path): 
                paths.append(path)
        for path in paths:
            for root, dirs, files in os.walk(path):
                for file in files:
                    if not file.endswith('.nfo'): continue
                    if file == "season.nfo" or file == "tvshow.nfo": continue
                    file_path = os.path.join(root, file)
                    # 处理文件名称
                    title = self.nfo_name_convert(file)
                    # 获取subject_id
                    subject_id = self.get_subject_id_by_title(title)
                    self.update_nfo(file_path, subject_id)

        self._is_runing_update_nfo = False
        logger.info("NFO文件更新完成")

    # 处理nfo文件名称，转换为媒体名称
    def nfo_name_convert(self, file_name: str) -> str:
        # 处理文件名称
        # 通过媒体文件获取媒体名称
        # 去除电影文件名的括号加年份
        title = re.sub(r'\([^()]*\)', '', file_name)
        # 去除文件名中的后缀
        title = os.path.splitext(title)[0]
        # 去除分辨率
        title = re.sub(r'\d{3,4}p', '', title)
        # 转换季数为中文
        title = self.name_season_convert(title)
        # 去除首尾空格
        title = title.strip()
        # 去除结尾的 "-"
        if title.endswith("-"):
            title = title[:-1]
        # 去除第X季之前的-和空格
        title = re.sub(r'-\s*第', '第', title)
        title = title.strip()
        return title
    
    # 更新订阅页面评分
    def update_subscribe_rank(self):
        if self._is_runing_update_rank: return
        self._is_runing_update_rank = True
        logger.info("开始更新订阅页面评分")
        db = ScopedSession
        results = db.query(Subscribe).all()
        for subscribe in results:
            # 取得Bangumi评分
            title = subscribe.name
            if(subscribe.season > 1):
                chinese_number = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]
                chinese_season = " 第" + chinese_number[subscribe.season - 1] + "季"
                title = title + chinese_season
            subject_id = self.search_subject(title)
            if subject_id == None: continue
            rank = self.get_rank(subject_id)
            if rank == None: continue
            # 更新订阅评分
            subscribe.vote = rank
        db.commit()
        db.close()
        logger.info("订阅页面评分更新完成")
        self._is_runing_update_rank = False

    # 去除名字中的 "S01" 和 "E0X" ，并将 "S02" 之后并转换为中文 第二季等
    def name_season_convert(self, name : str) -> str:
        string = name
        # 判断是否包含 "S02" 或者大于2的 "S0X"
        match = re.search(r'S(\d{2})', string)
        if match:
            season_number = int(match.group(1))
            if season_number >= 2:
                chinese_number = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]
                chinese_season = "第" + chinese_number[season_number - 1] + "季"
                string = re.sub(r'S\d{2}', chinese_season, string)

                # 去除 "E0X"
                string = re.sub(r'E\d{2}', '', string)
            # 去除 "S01"
            elif season_number == 1:
                string = re.sub(r'S01', '', string)
                # 去除 "E0X"
                string = re.sub(r'E\d{2}', '', string)
        return string 
    
    # 获取原始名称
    def get_original_title(self, name :str) -> str:
        if len(self._media_info) == 0: return None
        for info in self._media_info:
            if info['title'] == name:
                return info['original_title']
        return None
        
    def get_subject_id_by_title(self, title):
        """
        从缓存中获取条目ID
        """
        if len(self._media_info) == 0: return None
        for info in self._media_info:
            if title == info['title']:
                return info['subject_id']
        return None
    
    # 获取用户 Bangumi 上的 想看
    def get_wish(self):
        url = f"https://api.bgm.tv/v0/users/{self._bangumi_id}/collections?subject_type=2&type=1&limit=50&offset=0"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self._token}",
            "User-Agent": self._user_agent
        }
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            try:
                data = res.json().get("data")
            except (AttributeError, KeyError, TypeError):
                return None
            wish_list = []
            for item in data:
                logger.info(item.get("subject").get("name_cn"))
                wish_list.append(item.get("subject").get("name_cn"))
            return wish_list
        else:
            return None
        
    # 获取用户 Bangumi 上媒体的状态 1:想看 2:在看 3:看过 4:抛弃
    def get_collection_status(self, subject_id: str):
        url = f"https://api.bgm.tv/v0/users/{self._bangumi_id}/collections/{subject_id}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self._token}",
            "User-Agent": self._user_agent
        }
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            try:
                type = res.json().get("type")
            except (AttributeError, KeyError, TypeError):
                return None
            return type
        else:
            return None
    
    # 添加或者更新 media_info
    def add_or_update_media_info(self, media_info: dict):
        # 如果存在于缓存中则更新，否则添加
        if media_info["title"] in [subject["title"] for subject in self._media_info]:
            self._media_info = [subject for subject in self._media_info if subject["title"] != media_info["title"]]
            logger.info(f"更新缓存中的 {media_info['title']} 信息")
        else:
            self._media_info.append(media_info)
            logger.info(f"添加 {media_info['title']} 到缓存中")
        # 保存缓存
        self.save_data("mediainfo", self._media_info)

    @eventmanager.register(EventType.TransferComplete)
    def update_nfo_by_event(self, event):
        
        if not self._enabled or not self._update_nfo:
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
        title = raw_data.get("mediainfo").get("title")

        # logger.info(f"raw data: {raw_data}")

        # 开始处理入库文件
        for media_name in targets_file:
            file_name, file_ext = os.path.splitext(media_name)
            nfo_file = file_name + ".nfo"
            title = self.nfo_name_convert(file_name)
            subject_id = self.get_subject_id_by_title(title)
            if os.path.exists(nfo_file):
                self.update_nfo(nfo_file, subject_id)
            else:
                logger.error(f'{nfo_file} 不存在')

        

    def stop_service(self):
        """
        退出插件
        """
        try:
            if self._scheduler:
                self._scheduler.remove_all_jobs()
                if self._scheduler.running:
                    self._scheduler.shutdown()
                self._scheduler = None
        except Exception as e:
            logger.error("退出插件失败：%s" % str(e))

