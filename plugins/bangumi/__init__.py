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
from app.db.models import Base, db_update

from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session

from app.db import ScopedSession, Engine
from app.core.plugin import PluginManager

from plugins.bangumi.bangumi_db import BangumiInfo
from plugins.bangumi.bangumi_db_oper import BangumiOper

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
    plugin_version = "0.128"
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
    _sycn_subscribe_rating = False
    _update_nfo = False
    _update_nfo_all_once = False
    _library_path = ""
    _cron = ""
    _clear_cache = False

    _is_runing_sync = False
    _is_runing_update_nfo = False
    _is_runing_update_rating = False
    _is_runing_cache = False
    _bangumi_id = ""
    _max_thread = 100
    _cache_lock = threading.Lock()
    _sync_lock = threading.Lock()
    _user_agent = "hankunyu/moviepilot_plugin (https://github.com/HankunYu/MoviePilot-Plugins)"
    _scheduler: Optional[BackgroundScheduler] = None

    _oper = BangumiOper()
    mediainfo = {
        "title": None,
        "original_title": None,
        "subject_id": None,
        "rating": None,
        "status": None,
        "synced": False,
        "poster": None
    }
    def init_plugin(self, config: dict = None):
        self.check_table()
        if config:
            self._enabled = config.get("enabled")
            self._clear_cache = config.get("clear_cache")
            self._enable_sync = config.get("enable_sync")
            self._token = config.get("token")
            self._select_servers = config.get("select_servers")
            self._update_nfo = config.get("update_nfo")
            self._update_nfo_all_once = config.get("update_nfo_all_once")
            self._sycn_subscribe_rating = config.get("sync_subscribe_rating")
            self._library_path = config.get("library_path")
            self._cron = config.get("cron")
        
        # 清除缓存
        if self._clear_cache:
            self.clear_cache()
            self._clear_cache = False
            self.__update_config()
        if self._enabled:
            self.check_cache()
            self.login()
            logger.info("初始化Bangumi插件完成")
            self._scheduler = BackgroundScheduler(timezone=settings.TZ)
            # 定时任务
            if self._enable_sync:
                try:
                    self._scheduler.add_job(self.check_all_librarys_for_sync, 
                                            "interval",
                                            minutes=7200,
                                            name = "同步媒体库到Bangumi为已看")
                except Exception as e:
                    logger.error(f"定时任务添加失败: {e}")

            # 运行一次同步到Bangumi
            if self._enable_sync and not self._is_runing_sync and not self._is_runing_cache:
                thread = threading.Thread(target=self.check_all_librarys_for_sync)
                thread.start()
            
            # 更新全部NFO文件
            if self._update_nfo_all_once and not self._is_runing_update_nfo and not self._is_runing_cache:
                self._update_nfo_all_once = False
                self.__update_config()
                thread = threading.Thread(target=self.update_nfo_all_once)
                thread.start()

            # 更新订阅页面评分
            if self._sycn_subscribe_rating and not self._is_runing_update_rating:
                thread = threading.Thread(target=self.update_subscribe_rating)
                thread.start()

            # 启动定时任务
            if self._scheduler.get_jobs():
                self._scheduler.print_jobs()
                self._scheduler.start()
        else:
            try:
                if self._scheduler:
                    self._scheduler.remove_all_jobs()
                    if self._scheduler.running:
                        self._scheduler.shutdown()
                    self._scheduler = None
            except Exception as e:
                logger.error("关闭插件失败%s" % str(e))

    def check_table(self):
        """
        检查数据库是否存在
        """
        try:
            engine = Engine
            Base.metadata.create_all(engine)
        except Exception as e:
            logger.error(f"创建数据库失败: {e}")
            return False
        return True
    
    def __update_config(self):
        self.update_config({
            "enabled": self._enabled,
            "clear_cache": self._clear_cache,
            "enable_sync": self._enable_sync,
            "token": self._token,
            "select_servers": self._select_servers,
            "update_nfo": self._update_nfo,
            "update_nfo_all_once": self._update_nfo_all_once,
            "sync_subscribe_rating": self._sycn_subscribe_rating,
            "library_path": self._library_path,
            "cron": self._cron
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
                                            'model': 'sync_subscribe_rating',
                                            'label': '使用Bangumi评分更新订阅页面评分',
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
            "sync_subscribe_rating": False,
            "library_path": "",
        }

    def get_page(self) -> List[dict]:
        if self._oper.get_amount() == 0:
            return [
                {
                    'component': 'div',
                    'text': '暂无数据',
                    'props': {
                        'class': 'text-center'
                    }
                }
            ]
        info = self._oper.get_all_bangumi()
        contents_wish = []
        contents_watched = []
        contents_watching = []
        contents_dropped = []
        status_list = ["想看", "看过", "在看", "抛弃"]
        value = "tab"
        for item in info:
            content = ({
                'component': 'VCard',
                'content': [
                    {
                        'component': 'div',
                        'props': {
                            'class': 'd-flex justify-space-start flex-nowrap flex-row',
                        },
                        'content': [
                            {
                                'component': 'div',
                                'content': [
                                    {
                                        'component': 'VImg',
                                        'props': {
                                            'src': item.poster,
                                            'height': 120,
                                            'width': 80,
                                            'aspect-ratio': '2/3',
                                            'class': 'object-cover shadow ring-gray-500',
                                            'cover': True
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'div',
                                'content': [
                                    {
                                        'component': 'VCardSubtitle',
                                        'props': {
                                            'class': 'pa-2 font-bold break-words whitespace-break-spaces'
                                        },
                                        'content': [
                                            {
                                                'component': 'a',
                                                'props': {
                                                    'href': f"https://bangumi.tv/subject/{item.subject_id}",
                                                    'target': '_blank'
                                                },
                                                'text': item.title
                                            }
                                        ]
                                    },
                                    {
                                        'component': 'VCardText',
                                        'props': {
                                            'class': 'pa-0 px-2'
                                        },
                                        'text': f'状态：{status_list[int(item.status) - 1]}' if item.status != None else "状态：未收藏"
                                    },
                                    {
                                        'component': 'VCardText',
                                        'props': {
                                            'class': 'pa-0 px-2'
                                        },
                                        'text': f'评分：{item.rating}'
                                    }
                                ]
                            }
                        ]
                    }
                ]
            })
            if item.status == "1":
                contents_wish.append(content)
            elif item.status == "2":
                contents_watched.append(content)
            elif item.status == "3":
                contents_watching.append(content)
            elif item.status == "4":
                contents_dropped.append(content)
        """
        Tabs 不能与 VWindowItem 互动， 目测因为 v-model 值写死了？
        return [
            {
                'component': 'div',
                'content': [
                    {
                        "component": "VTabs",
                        "props": {
                            "model-value": value,
                            "grow": True,
                            "centered": True,
                            "class": "text-center"
                        },
                        "content": [
                            {
                                'component': 'VTab',
                                'props': {
                                    'value': 1,
                                },
                                'content': [
                                    {
                                        'component': 'VLabel',
                                        'props': {
                                            'text': '想看',
                                        }
                                    },
                                ]
                            },
                            {
                                'component': 'VTab',
                                'props': {
                                    'value': 2,
                                },
                                'content': [
                                    {
                                        'component': 'VLabel',
                                        'props': {
                                            'text': '看过',
                                        }
                                    },
                                ]
                            },
                            {
                                'component': 'VTab',
                                'props': {
                                    'value': 3,
                                },
                                'content': [
                                    {
                                        'component': 'VLabel',
                                        'props': {
                                            'text': '在看',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VTab',
                                'props': {
                                    'value': 4,
                                },
                                'content': [
                                    {
                                        'component': 'VLabel',
                                        'props': {
                                            'text': '抛弃',
                                        }
                                    }
                                ]
                            },
                        ]
                    },
                    {
                        'component': 'VWindow',
                        'props': {
                            "model-value": value,
                            "show-arrows": True,
                        },
                        'content': [
                            {
                                'component': 'VWindowItem',
                                'props': {
                                    'class': 'grid gap-3 grid-info-card',
                                    'value': 1,
                                },
                                'content': contents_wish
                            },
                            {
                                'component': 'VWindowItem',
                                'props': {
                                    'class': 'grid gap-3 grid-info-card',
                                    'value': 2,
                                },
                                'content': contents_watched
                            },
                            {
                                'component': 'VWindowItem',
                                'props': {
                                    'class': 'grid gap-3 grid-info-card',
                                    'value': 3,
                                },
                                'content': contents_watching
                            },
                            {
                                'component': 'VWindowItem',
                                'props': {
                                    'class': 'grid gap-3 grid-info-card',
                                    'value': 4,
                                },
                                'content': contents_dropped
                            },
                        ]
                    }
                ]
            }
        ]
        """
        return [
            {
                'component': 'div',
                'content': [
                    {
                        'component': 'VCardTitle',
                        'props': {
                        },
                        'content':[
                            {
                                component: 'VLabel',
                                props: {
                                    text: '想看',
                                }
                            }
                        ]
                    },
                    {
                        'component': 'div',
                        'props': {
                            'class': 'grid gap-3 grid-info-card',
                        },
                        'content': contents_wish
                    },
                    {
                        'component': 'VDivider',
                        'props': {
                            'thickness': 2,
                        }
                    },
                    {
                        'component': 'VCardTitle',
                        'props': {
                        },
                        'content':[
                            {
                                component: 'VLabel',
                                props: {
                                    text: '在看',
                                }
                            }
                        ]
                    },
                    {
                        'component': 'div',
                        'props': {
                            'class': 'grid gap-3 grid-info-card',
                        },
                        'content': contents_watching
                    },
                    {
                        'component': 'VDivider',
                        'props': {
                            'thickness': 2,
                        }
                    },
                    {
                        'component': 'VCardTitle',
                        'props': {
                        },
                        'content':[
                            {
                                component: 'VLabel',
                                props: {
                                    text: '看过',
                                }
                            }
                        ]
                    },
                    {
                        'component': 'div',
                        'props': {
                            'class': 'grid gap-3 grid-info-card',
                        },
                        'content': contents_watched
                    },
                    {
                        'component': 'VDivider',
                        'props': {
                            'thickness': 2,
                        }
                    },
                    {
                        'component': 'VCardTitle',
                        'props': {
                        },
                        'content':[
                            {
                                component: 'VLabel',
                                props: {
                                    text: '抛弃',
                                }
                            }
                        ]
                    },
                    {
                        'component': 'div',
                        'props': {
                            'class': 'grid gap-3 grid-info-card',
                        },
                        'content': contents_dropped
                    },
                ]
            }
        ]

    
    def check_cache(self):
        """
        检查缓存是否存在，不存在则初始化
        """
        if self._oper.get_amount() == 0: 
            logger.info("没有找到缓存，初始化列表")
            thread = threading.Thread(target=self.cache_library)
            thread.start()
    
    def clear_cache(self):
        """
        清除缓存
        """
        self._oper.empty()
        logger.info("清除缓存完成")

    # 缓存媒体库数据 需要保证其他函数不会在更新缓存时调用缓存
    def cache_library(self):
        if self._is_runing_cache: return
        self._is_runing_cache = True
        self._cache_lock.acquire()
        try:
            logger.info("开始缓存媒体库数据")
            results = self.get_medias_in_library()
            if len(results) == 0:
                logger.error("媒体库中没有找到媒体，请检查是否设置正确")
                return
            
            logger.info(f"共找到 {len(results)} 条媒体")
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
                        if self._oper.exists(title = media_info['title']):
                            # logger.info(f"{media_info['title']} 已存在于缓存中，跳过")
                            continue
                        media_info = self.get_bangumi_info(media_info)
                        logger.info(f"添加 {media_info['title']} 到缓存中, 条目ID: {media_info['subject_id']}, 评分: {media_info['rating']}, 状态: {media_info['status']}")
                        self._oper.add(**media_info)
                else:
                    # 如果已存在于缓存中，跳过
                    if self._oper.exists(title = media.title): 
                        # logger.info(f"{media.title} 已存在于缓存中，跳过")
                        continue
                    media_info["title"] = media.title
                    media_info["original_title"] = media.original_title
                    media_info = self.get_bangumi_info(media_info)
                    logger.info(f"添加 {media_info['title']} 到缓存中, 条目ID: {media_info['subject_id']}, 评分: {media_info['rating']}, 状态: {media_info['status']}")
                    self._oper.add(**media_info)
            logger.info("媒体库数据缓存完成")
        finally:
            self._is_runing_cache = False
            self._cache_lock.release()
        
    def check_all_librarys_for_sync(self):
        """
        同步全部媒体库到Bangumi
        """
        if self._is_runing_sync or self._is_runing_cache: return
        self._is_runing_sync = True
        self._sync_lock.acquire()
        try:
            # 更新缓存
            self.cache_library()
            if self._oper.get_amount() == 0:
                logger.info("媒体库中没有找到媒体，跳过同步全部媒体库")
                return
            logger.info("开始同步媒体库")
            for info in self._oper.get_all():
                self.sync_media_to_bangumi(info)
        finally:
            self._sync_lock.release()
            self._is_runing_sync = False
            logger.info("媒体库同步完成")

    def login(self):
        """
        登录Bangumi，获取用户UID
        """
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
    
    def get_bangumi_info(self, info: mediainfo):
        """
        获取Bangumi信息 需要传入 mediainfo
        """
        # 新建媒体信息
        new_media_info = self.mediainfo
        new_media_info["title"] = info['title']
        new_media_info["original_title"] = info['original_title']
        new_media_info["subject_id"] = None
        new_media_info["rating"] = None
        new_media_info["status"] = None
        new_media_info["synced"] = False
        new_media_info["poster"] = None

        # 获取条目ID
        subject_id = self.search_subject(new_media_info["title"])
        # 如果没有找到条目ID，尝试使用原始名称
        if subject_id == None:
            subject_id = self.search_subject(new_media_info["original_title"])
        # 如果没有找到条目ID，跳过
        if subject_id == None:
            return new_media_info
        new_media_info["subject_id"] = subject_id
        # 获取海报
        new_media_info["poster"] = self.get_poster(subject_id)
        # 获取评分
        new_media_info['rating'] = self.get_rating(subject_id)
        # 检查收藏状态
        status = self.get_collection_status(subject_id)
        new_media_info["status"] = status
        # copy是否已同步
        new_media_info["synced"] = info["synced"]
        return new_media_info

    # 同步番剧到 Bangumi 为已看
    def sync_media_to_bangumi(self, info: BangumiInfo):
        """
        同步番剧到 Bangumi 为已看
        """
        media_info = self.mediainfo
        media_info["title"] = info.title
        media_info["original_title"] = info.original_title
        media_info["subject_id"] = info.subject_id
        media_info["rating"] = info.rating
        media_info["status"] = info.status
        media_info["synced"] = info.synced
        media_info["poster"] = info.poster

        # 如果已同步，跳过
        if media_info["synced"] == True: 
            # logger.info(f"{media_info['title']}已同步，跳过")
            return
        # 如果没有条目ID，跳过
        if media_info["subject_id"] == None:
            # logger.info(f"{media_info['title']} 无法在Bangumi上找到，跳过")
            return
        # 如果已收藏，跳过
        if media_info["status"] != None:
            # logger.info(f"{media_info['title']}已收藏，跳过")
            media_info["synced"] = True
            self._oper.update_info(**media_info)
            return
        # 添加收藏 为已看
        if self.add_collections(media_info["subject_id"]):
            media_info["synced"] = True
            media_info["status"] = 3
            if self._oper.update_info(**media_info): logger.info(f"{media_info['title']}收藏成功")
        else:
            logger.info(f"{media_info['title']}收藏失败")
    
    # 获取媒体库中的媒体 目标为数据库中的 MediaServerItem 表
    def get_medias_in_library(self):
        db = ScopedSession

        results = db.query(MediaServerItem).filter(
            MediaServerItem.server.in_(self._select_servers)
        ).all()

        db.close()
        return results      

    def search_subject(self, name: str):
        """
        获取名字对应的条目ID 将移除特殊字符后进行匹配
        """
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
    
    def get_poster(self, subject_id: str):
        """
        获取条目海报
        """
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
                poster = res.json().get("images").get("common")
            except (AttributeError, KeyError, TypeError):
                return None
            return poster
        else:
            return None
    
    def get_rating(self, subject_id: str):
        """
        获取条目评分
        """
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
                rating = res.json().get("rating").get("score")
            except (AttributeError, KeyError, TypeError):
                return None
            return res.json().get("rating").get("score") == 0 and 0 or res.json().get("rating").get("score")
        else:
            return None
    
    def check_subject_in_collections(self, subject_id: str):
        """
        检查 Bangumi 是否已收藏
        """
        return self.get_collection_status(subject_id) is not None

    def add_collections(self, subject_id: str):
        """
        添加收藏
        """
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
        rating = self.get_rating(subject_id)
        if rating == None: return False

        # 更新NFO
        if not os.path.exists(file_path):
            return False
        with open(file_path, 'r') as file:
            content = file.read()
        content = re.sub(r'<rating>.*?</rating>', f'<rating>{rating}</rating>', content)
        if re.search(r'<rating>.*?</rating>', content) == None:
            logger.info(f"{file_path} 中没有rating字段")
            return False
        with open(file_path, 'w') as file:
            file.write(content)
            logger.info(f"更新{file_path}的评分为{rating}")
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

   
    def nfo_name_convert(self, file_name: str) -> str:
        """
        处理nfo文件名称，转换为媒体名称
        """
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
    def update_subscribe_rating(self):
        if self._is_runing_update_rating: return
        self._is_runing_update_rating = True
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
            rating = self.get_rating(subject_id)
            if rating == None: continue
            # 更新订阅评分
            subscribe.vote = rating
        db.commit()
        db.close()
        logger.info("订阅页面评分更新完成")
        self._is_runing_update_rating = False

    
    def name_season_convert(self, name : str) -> str:
        """
        去除名字中的 "S01" 和 "E0X" ，并将 "S02" 之后并转换为中文 第二季等
        """
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
    
    def get_original_title(self, name :str) -> str:
        """
        通过名字获取原始名称
        """
        return self._oper.get_original_title(title = name)
        
    def get_subject_id_by_title(self, title):
        """
        从缓存中获取条目ID
        """
        if title == None: return None
        return self._oper.get_subject_id(title = title)
    
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