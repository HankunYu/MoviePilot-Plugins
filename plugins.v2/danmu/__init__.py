# MoviePilot library
from app.log import logger
from app.plugins import _PluginBase
from app.core.event import eventmanager
from app.schemas.types import EventType
from app.utils.system import SystemUtils
from app.chain.media import MediaChain
from app.core.metainfo import MetaInfo
from app.core.config import settings
from app import schemas
from app.schemas.types import MediaType, EventType, SystemConfigKey
from datetime import datetime, timedelta

from typing import Any, List, Dict, Tuple, Optional
import subprocess
import os
import threading
import time
import json
import copy
from app.plugins.danmu import danmu_generator as generator
   

class Danmu(_PluginBase):
    # 插件名称
    plugin_name = "弹幕刮削"
    # 插件描述
    plugin_desc = "使用弹弹play平台生成弹幕的字幕文件，实现弹幕播放。"
    # 插件图标
    plugin_icon =  "https://raw.githubusercontent.com/HankunYu/MoviePilot-Plugins/main/icons/danmu.png"
    # 主题色
    plugin_color = "#3B5E8E"
    # 插件版本
    plugin_version = "1.11.0"
    # 插件作者
    plugin_author = "hankun"
    # 作者主页
    author_url = "https://github.com/hankunyu"
    # 插件配置项ID前缀
    plugin_config_prefix = "danmu_"
    # 加载顺序
    plugin_order = 1
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _enabled = False
    _width = 1920
    _height = 1080
    # 搞字体太复杂 以后再说
    # _fontface = 'Arial'
    _fontsize = 50
    _alpha = 0.8
    _duration = 15
    _path = ''
    _max_threads = 10
    _onlyFromBili = False
    _useTmdbID = True
    _auto_scrape = True
    _screen_area = 'full'  # full(全屏), half(半屏), quarter(1/4屏)
    _enable_strm = True  # 是否启用.strm文件刮削
    # 新增重试相关配置
    _min_danmu_count = 100  # 最小弹幕数量要求 - 硬编码
    # 复查退避（小时）：按结局分档，随连续未成功次数指数增长，只有间隔上限、
    # 没有次数上限——「老片后来被收录」永远覆盖得到，只是不必每 3 小时问一次
    _backoff_base_hours = {
        "failed": 1,     # 网络/数据异常，多半是暂时的
        "empty": 3,      # 已收录但暂无弹幕，新番很快会有
        "absent": 24,    # 确认无收录，弹弹play 很少突然补上
    }
    _backoff_ok_recent_hours = 6       # 新番已有弹幕，但还会继续涨
    _backoff_cap_recent_hours = 24     # 新番退避封顶
    _backoff_cap_hours = 24 * 30       # 其余封顶
    _enable_retry_task = True  # 是否启用重试任务
    _stop_wait_seconds = 30  # stop_service 等待批量刮削收尾的最长时间
    _ui_acquire_timeout = 10  # UI请求等待限速令牌的上限，超时即提示稍后再试
    
    # 刮削状态库：{file_path: {verdict, comment_id, danmu_count, attempts,
    #                        last_attempt, last_success, release_date, render}}
    # 存 save_data 而非配置——配置每次保存都整体重写，大库上万条会拖垮它
    _scrape_state: Dict[str, Dict[str, Any]] = {}
    _scrape_state_key = "scrape_state"
    # init_plugin 暂存的旧版 retry_tasks，仅用于一次性迁移
    _legacy_retry_tasks: Optional[str] = None
    _state_lock = threading.Lock()
    _state_save_deferred = False
    _state_save_pending = False
    # 系列级缓存：{f"{tmdb_id}:{type}": {series, fetched_at, ttl_hours}}
    _series_cache: Dict[str, Dict[str, Any]] = {}
    _series_cache_key = "series_cache"
    _series_save_pending = False
    _series_ttl_recent_hours = 6           # 新番：条目和弹幕都还在变
    _series_ttl_hours_default = 24 * 30    # 已收录的完结作品
    _series_ttl_absent_hours = 24 * 30     # 确认无收录，但仍定期复查
    # 正在刮削中的文件集合，防止同一文件被并发刮削写坏弹幕文件
    _inflight_lock = threading.Lock()
    _inflight_files: set = set()
    # 批量刮削进度状态（含全局定时刮削与目录刮削）
    _scrape_lock = threading.Lock()
    # 插件停止信号；批量刮削与重试任务在每个文件前检查，保证 stop_service 能收尾
    _stop_event = threading.Event()
    _scrape_thread: Optional[threading.Thread] = None
    _scrape_progress: Dict[str, Any] = {
        "running": False,
        "total": 0,
        "processed": 0,
        "success": 0,
        "failed": 0,
        "absent": 0,
        "empty": 0,
        "deferred": 0,
        "skipped": 0,
        "current_file": None,
        "started_at": None,
        "duration": 0
    }
    _manual_matches: Dict[str, Dict[str, Any]] = {}
    _manual_file_matches: Dict[str, Dict[str, Any]] = {}
    # Negative cache: directories confirmed to have no manual match (avoids repeated disk checks while browsing)
    _manual_match_misses: set = set()
    # Danmu line-count cache: {ass_path: (mtime_ns, size, count)} — skip re-reading unchanged files
    _danmu_count_cache: Dict[str, Tuple[int, int, int]] = {}
    _manual_match_storage_key = "manual_matches"

    media_chain = MediaChain()

    @property
    def _manual_match_filename(self) -> str:
        return generator.DanmuAPI.MANUAL_MATCH_FILE

    def _normalize_path(self, path: Optional[str]) -> Optional[str]:
        if not path:
            return None
        return os.path.normpath(path)

    def _manual_json_path(self, directory: str) -> str:
        return os.path.join(directory, self._manual_match_filename)

    def _configured_roots(self) -> List[str]:
        """
        配置的刮削根路径列表（绝对化并折叠 ..；不解析符号链接，
        以免软链接方式整理的媒体库被判为越界）
        """
        if not self._path:
            return []
        return [os.path.abspath(os.path.normpath(p.strip()))
                for p in self._path.split('\n') if p.strip()]

    def _resolve_in_roots(self, path: Optional[str]) -> Optional[str]:
        """
        将API传入的路径限制在配置的根路径内
        :param path: 外部传入的路径
        :return: 规范化后的绝对路径；越界或未配置根路径时返回None
        """
        if not path:
            return None
        roots = self._configured_roots()
        if not roots:
            logger.warning("未配置刮削路径，拒绝访问任意路径")
            return None
        target = os.path.abspath(os.path.normpath(path))
        for root in roots:
            if target == root or target.startswith(root + os.sep):
                return target
        logger.warning(f"路径超出配置的刮削范围，已拒绝: {path}")
        return None

    def _save_manual_state(self):
        try:
            payload = {
                "directories": self._manual_matches,
                "files": self._manual_file_matches
            }
            self.save_data(self._manual_match_storage_key, payload)
        except Exception as e:
            logger.warning(f"保存手动匹配状态失败: {e}")

    def _load_manual_matches(self):
        stored = self.get_data(self._manual_match_storage_key)
        if not isinstance(stored, dict):
            stored = {}

        # 兼容旧版本仅存储目录映射的结构
        if "directories" in stored or "files" in stored:
            dir_data = stored.get("directories", {})
            file_data = stored.get("files", {})
        else:
            dir_data = stored
            file_data = {}

        self._manual_matches = {}
        self._manual_file_matches = {}
        self._manual_match_misses = set()

        for raw_path, info in dir_data.items():
            norm = self._normalize_path(raw_path)
            if not norm:
                continue
            payload = self._normalize_manual_entry(info, scope="directory")
            if payload:
                self._manual_matches[norm] = payload

        for raw_path, info in file_data.items():
            norm = self._normalize_path(raw_path)
            if not norm:
                continue
            payload = self._normalize_manual_entry(info, scope="file")
            if payload:
                self._manual_file_matches[norm] = payload

    @staticmethod
    def _normalize_manual_entry(data: Any, scope: str) -> Optional[Dict[str, Any]]:
        if not isinstance(data, dict):
            return None
        anime_id = data.get("animeId") or data.get("anime_id")
        if anime_id is None:
            return None
        try:
            anime_id = int(anime_id)
        except (TypeError, ValueError):
            return None
        payload = dict(data)
        payload["animeId"] = anime_id
        payload.pop("anime_id", None)
        payload["scope"] = scope
        offset = payload.get("episodeOffset")
        if offset is not None:
            try:
                payload["episodeOffset"] = int(offset)
            except (TypeError, ValueError):
                payload.pop("episodeOffset", None)
        payload.setdefault("updatedAt", datetime.now().isoformat(timespec="seconds"))
        return payload

    @staticmethod
    def _clone_manual_match(data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not data:
            return None
        return copy.deepcopy(data)

    def _convert_legacy_id_file(self, directory: str) -> Optional[Dict[str, Any]]:
        try:
            for entry in os.listdir(directory):
                if not entry.endswith('.id'):
                    continue
                legacy_path = os.path.join(directory, entry)
                try:
                    anime_id = int(os.path.splitext(entry)[0])
                except (TypeError, ValueError):
                    logger.warning(f"忽略无法解析的ID文件: {legacy_path}")
                    continue
                match_info = {
                    "animeId": int(anime_id),
                    "source": "legacy-id-file",
                    "updatedAt": datetime.now().isoformat(timespec="seconds")
                }
                self._write_manual_match_file(directory, match_info)
                try:
                    os.remove(legacy_path)
                    logger.info(f"已转换旧的ID文件并删除: {legacy_path}")
                except Exception as e:
                    logger.warning(f"删除旧ID文件失败: {e}")
                return match_info
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.warning(f"转换旧ID文件失败: {e}")
        return None

    def _write_manual_match_file(self, directory: str, data: Dict[str, Any]):
        if not directory:
            return
        try:
            generator.DanmuAPI._write_manual_mapping(directory, data)
        except AttributeError:
            # 回退写入逻辑
            try:
                os.makedirs(directory, exist_ok=True)
                anime_id = data.get("animeId") or data.get("anime_id")
                if anime_id is None:
                    return
                payload = dict(data)
                payload["animeId"] = int(anime_id)
                payload.pop("anime_id", None)
                payload["scope"] = "directory"
                payload.setdefault("updatedAt", datetime.now().isoformat(timespec="seconds"))
                with open(self._manual_json_path(directory), 'w', encoding='utf-8') as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"写入手动匹配文件失败: {e}")

    def _update_manual_match_cache(self, directory: str, data: Optional[Dict[str, Any]]):
        norm = self._normalize_path(directory)
        if not norm:
            return
        if data:
            payload = self._normalize_manual_entry(data, scope="directory")
            if not payload:
                return
            self._manual_matches[norm] = payload
        else:
            self._manual_matches.pop(norm, None)
        self._manual_match_misses.discard(norm)
        self._save_manual_state()

    def _update_manual_file_match_cache(self, file_path: str, data: Optional[Dict[str, Any]]):
        norm = self._normalize_path(file_path)
        if not norm:
            return
        if data:
            payload = self._normalize_manual_entry(data, scope="file")
            if not payload:
                return
            self._manual_file_matches[norm] = payload
        else:
            self._manual_file_matches.pop(norm, None)
        self._save_manual_state()

    def _get_manual_match(self, directory: str, check_legacy: bool = True,
                          use_miss_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        获取目录的手动匹配信息
        :param directory: 目录路径
        :param check_legacy: 是否检查旧版.id文件（需要列目录，浏览场景应关闭）
        :param use_miss_cache: 是否信任「该目录没有手动匹配」的负缓存。
                               刮削时应关闭：用户可能直接在磁盘上放了
                               .dandan.anime.json，负缓存会让它一直不生效。
                               浏览时保留，那只是徽标晚一次刷新。
        """
        if not directory:
            return None
        norm = self._normalize_path(directory)
        cached = self._manual_matches.get(norm)
        if cached:
            return self._clone_manual_match(cached)
        if use_miss_cache and norm in self._manual_match_misses:
            return None
        if not os.path.isdir(directory):
            return None

        manual_path = self._manual_json_path(directory)
        if os.path.exists(manual_path):
            try:
                with open(manual_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._update_manual_match_cache(directory, data)
                return self._clone_manual_match(self._manual_matches.get(norm))
            except Exception as e:
                logger.warning(f"读取手动匹配文件失败: {e}")

        if check_legacy:
            legacy = self._convert_legacy_id_file(directory)
            if legacy:
                self._update_manual_match_cache(directory, legacy)
                return self._clone_manual_match(self._manual_matches.get(norm))

        self._manual_match_misses.add(norm)
        return None

    def _resolve_manual_comment_id(self, file_path: str, episode: Optional[int]) -> Optional[str]:
        """
        解析该文件的手动匹配，拼出弹幕ID。单文件匹配优先于所属目录的匹配。

        手动匹配的解析统一收在插件层这一处：它需要 MetaInfo 的上下文，也需要
        插件的匹配缓存，而 generator 两者都没有——此前目录级匹配放在 generator 里
        每次读盘，还导致它对 .strm 文件整条路径都走不到。
        :param file_path: 媒体文件路径
        :param episode: 本地集号（会应用集数偏移）
        :return: 弹幕ID；没有手动匹配或数据无效时返回None，调用方走常规匹配
        """
        for match, scope in (
            (self._get_manual_file_match(file_path), "单文件"),
            (self._get_manual_match(os.path.dirname(file_path), use_miss_cache=False), "目录"),
        ):
            if not match:
                continue
            manual_episode = generator.DanmuAPI._apply_episode_offset(
                episode, match.get("episodeOffset")
            )
            comment_id = generator.DanmuAPI._compose_comment_id(
                match.get("animeId"), manual_episode
            )
            if comment_id:
                logger.info(f"使用{scope}手动匹配ID: {comment_id}")
                return comment_id
            logger.warning(f"{scope}手动匹配无法拼出弹幕ID，回退常规匹配: {match}")
        return None

    def _get_manual_file_match(self, file_path: str) -> Optional[Dict[str, Any]]:
        norm = self._normalize_path(file_path)
        if not norm:
            return None
        cached = self._manual_file_matches.get(norm)
        if cached:
            return self._clone_manual_match(cached)
        return None

    def _resolve_manual_directory(self, file_path: Optional[str] = None, directory_path: Optional[str] = None) -> Optional[str]:
        if directory_path:
            return self._normalize_path(directory_path)
        if file_path:
            return self._normalize_path(os.path.dirname(file_path))
        return None
    
    def _is_supported_file(self, file_path: str) -> bool:
        """检查文件是否支持处理"""
        if file_path.endswith(('.mp4', '.mkv')):
            return True
        elif file_path.endswith('.strm'):
            return self._enable_strm
        return False
    
    @staticmethod
    def _clamp_max_threads(value: Any) -> int:
        """
        并发数只影响本地开销（ffprobe取时长、算MD5、生成与合并字幕），
        对服务端的压力由请求层令牌桶控制，两者互不替代
        """
        try:
            return max(1, min(int(value), 32))
        except (TypeError, ValueError):
            logger.warning(f"并发数配置无效({value})，使用默认值10")
            return 10

    def _apply_config(self, config: dict):
        """
        将配置字典写入内存属性（不含重试任务，重试任务只在加载时解析）
        """
        self._enabled = config.get("enabled", False)
        self._width = config.get("width", 1920)
        self._height = config.get("height", 1080)
        # self._fontface = config.get("fontface")
        self._fontsize = config.get("fontsize", 50)
        self._alpha = config.get("alpha", 0.8)
        self._duration = config.get("duration", 15)
        self._path = config.get("path", "")
        self._max_threads = self._clamp_max_threads(config.get("max_threads", 10))
        self._onlyFromBili = config.get("onlyFromBili", False)
        self._useTmdbID = config.get("useTmdbID", True)
        self._auto_scrape = config.get("auto_scrape", False)
        self._enable_retry_task = config.get("enable_retry_task", True)
        self._screen_area = config.get("screen_area", "full")
        self._enable_strm = config.get("enable_strm", True)

    def init_plugin(self, config: dict = None):
        self._stop_event.clear()
        # 让弹弹API的User-Agent跟随插件版本，避免版本号多处手工同步
        generator.DanmuAPI.set_client_version(self.plugin_version)
        # 重新加载时清空上一轮遗留的限流闸门，并重新探测环境
        # （用户可能刚装上 ffmpeg）
        generator.DanmuAPI.reset_gate()
        generator.DanmuAPI.reset_environment_probe()
        if config:
            self._apply_config(config)
            self._legacy_retry_tasks = config.get("retry_tasks")
        # 加载刮削状态库与手动匹配缓存
        self._load_scrape_state()
        self._load_series_cache()
        self._load_manual_matches()
        if self._enabled:
            logger.info("弹幕加载插件已启用")

    def get_state(self) -> bool:
        return self._enabled
    
    def get_service(self) -> List[Dict[str, Any]]:
        """
        注册插件公共服务
        [{
            "id": "服务ID",
            "name": "服务名称",
            "trigger": "触发器：cron/interval/date/CronTrigger.from_crontab()",
            "func": self.xxx,
            "kwargs": {} # 定时器参数
        }]
        """
        if self._enabled and self._enable_retry_task:
            return [{
                "id": "DanmuRetryTask",
                "name": "弹幕重试任务",
                "trigger": "cron",
                "func": self.auto_process_retry_tasks,
                "kwargs": {
                    "minute": 0,
                    "hour": "*/3",  # 每3小时执行一次
                    "day": "*",
                    "month": "*",
                    "day_of_week": "*"
                }
            }]
        return []
        
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
        logger.info("获取插件API")
        return [{
            "path": "/generate_danmu_with_path",
            "endpoint": self.generate_danmu_global,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "刮削弹幕",
            "description": "根据设定的路径刮削弹幕" 
        },{
            "path": "/update_path",
            "endpoint": self.update_path,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "更新路径",
            "description": "更新刮削路径"
        },
        {
            "path": "/config",
            "endpoint": self._get_config,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "获取配置",
            "description": "获取插件配置"
        },
        {
            "path": "/config",
            "endpoint": self._save_config,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "保存配置",
            "description": "保存插件配置"
        },
        {
            "path": "/status",
            "endpoint": self._get_status,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "获取状态",
            "description": "获取当前刮削状态"
        },
        {
            "path": "/scan_path",
            "endpoint": self.scan_path,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "扫描路径",
            "description": "扫描路径下的媒体文件和弹幕信息，支持current_dir参数进行点击式导航"
        },
        {
            "path": "/scan_subfolder",
            "endpoint": self.scan_subfolder,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "扫描子文件夹",
            "description": "扫描指定子文件夹的内容"
        },
        {
            "path": "/generate_danmu",
            "endpoint": self.generate_danmu_single,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "生成单个文件弹幕",
            "description": "为指定文件生成弹幕"
        },
        {
            "path": "/scrape_directory",
            "endpoint": self.scrape_directory,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "刮削整个目录",
            "description": "后台批量刮削指定目录下所有媒体文件，需要directory_path参数"
        },
        {
            "path": "/retry_tasks",
            "endpoint": self.get_retry_tasks,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "获取重试任务列表",
            "description": "获取当前待重试的弹幕文件列表"
        },
        {
            "path": "/process_retry_tasks",
            "endpoint": self.process_retry_tasks,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "处理重试任务",
            "description": "对重试任务列表中的文件进行弹幕刮削"
        },
        {
            "path": "/clear_retry_tasks",
            "endpoint": self.clear_retry_tasks,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "清空重试任务",
            "description": "清空所有重试任务"
        },
        {
            "path": "/remove_retry_task",
            "endpoint": self.remove_retry_task,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "移除重试任务",
            "description": "移除指定的重试任务，需要file_path参数"
        },
        {
            "path": "/search_anime",
            "endpoint": self.search_anime,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "搜索弹弹番剧",
            "description": "根据关键字搜索手动匹配候选"
        },
        {
            "path": "/manual_match",
            "endpoint": self.set_manual_match,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "保存手动匹配",
            "description": "为目录保存手动匹配的弹弹作品"
        },
        {
            "path": "/remove_manual_match",
            "endpoint": self.remove_manual_match,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "移除手动匹配",
            "description": "移除指定目录的手动匹配"
        }
        ]
     
    # 插件配置页面
    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        return None, self._get_config()
    
    def _get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return {
            "enabled": self._enabled,
            "width": self._width,
            "height": self._height,
            "fontsize": self._fontsize,
            "alpha": self._alpha,
            "duration": self._duration,
            "path": self._path,
            "max_threads": self._max_threads,
            "onlyFromBili": self._onlyFromBili,
            "useTmdbID": self._useTmdbID,
            "auto_scrape": self._auto_scrape,
            "enable_retry_task": self._enable_retry_task,
            "screen_area": self._screen_area,
            "enable_strm": self._enable_strm
        }
        
    def _persist_config(self):
        """将当前内存配置连同重试任务写回系统配置（所有落盘的唯一入口）"""
        # 刮削状态另存 save_data，不再塞进配置——配置每次保存都整体重写
        self.update_config(self._get_config())

    def _save_config(self, config: dict):
        """保存配置"""
        try:
            self._apply_config(config)
            self._persist_config()
            return schemas.Response(success=True, message="配置已保存")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return schemas.Response(success=False, message=f"保存配置失败: {str(e)}")
    
    def get_page(self) -> List[dict]:
        """Vue mode doesn't use Vuetify page definitions."""
        return None
    
    # --- V2 Vue Interface Method ---
    @staticmethod
    def get_render_mode() -> Tuple[str, Optional[str]]:
        """Declare Vue rendering mode and assets path."""
        return "vue", "dist/assets"
    
    def _get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        with self._scrape_lock:
            progress = dict(self._scrape_progress)
        if progress.get("running") and progress.get("started_at"):
            progress["duration"] = int(time.time() - progress["started_at"])
        progress.pop("started_at", None)
        return {
            "enabled": self._enabled,
            **progress
        }

    def generate_danmu(self, file_path: str) -> generator.DanmuResult:
        """
        生成弹幕文件（同一文件同时只允许一个刮削，防止并发写坏弹幕文件）
        :param file_path: 视频文件路径
        :return: 刮削结果分类
        """
        norm = self._normalize_path(file_path) or file_path
        with self._inflight_lock:
            if norm in self._inflight_files:
                logger.info(f"文件正在刮削中，跳过重复请求: {file_path}")
                return generator.DanmuResult("failed", message="文件正在刮削中，跳过重复请求")
            self._inflight_files.add(norm)
        try:
            return self._generate_danmu_impl(file_path)
        finally:
            with self._inflight_lock:
                self._inflight_files.discard(norm)

    @staticmethod
    def _parse_episode(meta: Any) -> Optional[int]:
        """
        取媒体识别结果中的集号。
        直接用 begin_episode 而非解析 episode 字符串：双集文件（E13-E14）
        天然取首集，也不会把合法的第0集当成假值丢掉。
        :param meta: MetaInfo 识别结果
        :return: 集号；无集数信息（如电影）时返回None
        """
        episode = getattr(meta, "begin_episode", None)
        if episode is None:
            return None
        try:
            return int(episode)
        except (TypeError, ValueError):
            logger.warning(f"集号无法解析: {episode!r}")
            return None

    def _generate_danmu_impl(self, file_path: str) -> generator.DanmuResult:
        meta = MetaInfo(file_path)
        tmdb_id = None
        episode = None
        season = None
        tmdb_id_type = 0
        release_date = None
        use_short_cache_ttl = False
        if self._useTmdbID:
            media_info = self.media_chain.recognize_media(meta=meta)
            if media_info:
                tmdb_id = media_info.tmdb_id
                # Matches dandanplay upstream tmdbIdType: 0 = TV series, 1 = movie
                if media_info.type == MediaType.MOVIE:
                    tmdb_id_type = 1
                    logger.info(f"识别为电影，使用电影类型TMDB匹配: {tmdb_id}")
                episode = self._parse_episode(meta)
                season = getattr(meta, "begin_season", None)
                release_date = media_info.release_date
                if self._is_recent_release(release_date):
                    logger.info(f"媒体 {tmdb_id} 是最近90天内发布的内容,使用短缓存")
                    use_short_cache_ttl = True

        manual_comment_id = self._resolve_manual_comment_id(file_path, episode)
        if not manual_comment_id:
            # 整季查询排在 /match 之前：命中缓存时定位一集是零请求，
            # 且「这一集在不在列表里」本身就是确定性答案，不必再问服务端。
            # /match 只在这里解决不了时兜底（拿不到 tmdb_id、集号映射不上）
            manual_comment_id = self._locate_via_series(
                tmdb_id, tmdb_id_type, season, episode, release_date, file_path)
            if manual_comment_id is self._SERIES_ABSENT:
                absent = generator.DanmuResult("absent", message="弹弹play未收录该内容")
                # 这条结论同样要落状态库，否则整季查询判出的 absent 反而不会被记住
                self._record_scrape_state(file_path, absent, release_date)
                return absent

        try:
            result = generator.danmu_generator(
                file_path,
                self._width,
                self._height,
                'Arial',
                self._fontsize,
                self._alpha,
                self._duration,
                self._onlyFromBili,
                self._useTmdbID,
                tmdb_id,
                episode,
                60 if use_short_cache_ttl else None,
                self._screen_area,
                manual_comment_id=manual_comment_id,
                tmdb_id_type=tmdb_id_type,
                min_danmu_count=self._min_danmu_count
            )
            
            # 弹幕数量判断只能用服务端返回的数量（过滤前），
            # 本地 .ass 行数掺了 onlyFromBili 之类的本地过滤，不能用来推断服务端状态
            if result.is_ok and result.danmu_count >= self._min_danmu_count:
                logger.info(f"弹幕生成完成，弹幕数量: {result.danmu_count}")
            else:
                # ok 但数量不足、empty（已收录暂无弹幕）、absent、failed 都留待复查。
                # absent 目前也进重试列表以保留「弹弹play 之后收录了」的恢复路径，
                # v1.11.0 的状态库会用系列级退避取代这个每 3 小时一次的轮询。
                if result.outcome != "ok":
                    logger.info(f"{result.message} - {file_path}")
            self._record_scrape_state(file_path, result, release_date)

            return result
        except generator.DanmuThrottled:
            # 服务端拒绝了请求，这不代表没有弹幕：不进重试列表，否则服务端
            # 每拦一次客户端就多排一次重试，越限流请求越多
            raise
        except generator.DanmuUnresolvable:
            # 条件不变则结果不变，重试没有意义，同样不进重试列表
            raise
        except Exception as e:
            logger.error(f"生成弹幕失败: {e}")
            failure = generator.DanmuResult("failed", message=f"生成弹幕失败: {str(e)}")
            self._record_scrape_state(file_path, failure, release_date)
            return failure

    # ------------------------------------------------------------------
    # 刮削状态库
    #
    # 每个文件记三档，失效条件各不相同：
    #   识别状态 comment_id —— 只有弹弹play 重编条目才失效
    #   内容状态 danmu_count（服务端返回、本地过滤前）—— 随时间失效
    #   渲染状态 render —— 产出该 .ass 时的配置，配置一改就失效
    # 此前这三样一样都没存，导致「没收录 / 收录了但没弹幕 / 没刮过」在磁盘上
    # 完全不可分辨（都是没有 .ass 文件），只能每轮全部重问。
    # ------------------------------------------------------------------

    def _render_signature(self) -> Dict[str, Any]:
        """当前影响弹幕文件产出的配置，用于判断存量 .ass 是否需要重新生成"""
        return {
            "onlyFromBili": self._onlyFromBili,
            "screen_area": self._screen_area,
            "fontsize": self._fontsize,
            "alpha": self._alpha,
            "duration": self._duration,
            "width": self._width,
            "height": self._height,
        }

    def _load_scrape_state(self):
        """加载状态库；首次运行时从旧的 retry_tasks 配置迁移"""
        stored = self.get_data(self._scrape_state_key)
        # 先清空：插件重载时不能把上一轮的内存状态留下来
        with self._state_lock:
            self._scrape_state = {}
        if isinstance(stored, dict) and stored:
            with self._state_lock:
                self._scrape_state = {
                    self._normalize_path(k): v for k, v in stored.items()
                    if isinstance(v, dict) and self._normalize_path(k)
                }
            logger.info(f"加载了 {len(self._scrape_state)} 条刮削状态")
            return
        migrated = self._migrate_retry_tasks()
        if migrated:
            logger.info(f"已从旧的重试任务迁移 {migrated} 条刮削状态")
            self._flush_scrape_state(force=True)

    def _migrate_retry_tasks(self) -> int:
        """把旧版存在配置里的 retry_tasks 迁进状态库"""
        raw = getattr(self, "_legacy_retry_tasks", None)
        if not raw:
            return 0
        try:
            legacy = json.loads(raw)
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.warning(f"旧重试任务无法解析，跳过迁移: {e}")
            return 0
        if not isinstance(legacy, dict):
            return 0
        with self._state_lock:
            for file_path, task in legacy.items():
                norm = self._normalize_path(file_path)
                if not norm or not isinstance(task, dict):
                    continue
                self._scrape_state[norm] = {
                    "verdict": "failed",
                    "comment_id": None,
                    "danmu_count": int(task.get("last_danmu_count", 0) or 0),
                    "attempts": int(task.get("retry_count", 1) or 1),
                    "last_attempt": task.get("last_attempt"),
                    "last_success": None,
                    "release_date": None,
                    "render": None,
                }
            return len(self._scrape_state)

    def _flush_scrape_state(self, force: bool = False):
        """
        落盘状态库。批量刮削期间只标记待保存、结束时统一写一次——
        大库有上万条，每个文件都整体重写会拖垮批量刮削。
        """
        try:
            if not force:
                with self._state_lock:
                    if self._state_save_deferred:
                        self._state_save_pending = True
                        return
            with self._state_lock:
                snapshot = copy.deepcopy(self._scrape_state)
            self.save_data(self._scrape_state_key, snapshot)
            logger.debug(f"刮削状态已保存（{len(snapshot)} 条）")
        except Exception as e:
            logger.error(f"保存刮削状态失败: {e}")

    def _compute_next_check(self, verdict: str, attempts: int, satisfied: bool,
                            release_date: Optional[str]) -> str:
        """
        算出下次复查时间。指数退避取代了原来的「重试 10 次就放弃」——
        那个硬截断既会在新番弹幕正涨时提前放弃，又会被下一次全局刮削原样加回来，
        形成无限循环。退避没有上限次数，只有间隔上限，所以「老片后来被收录」
        这类情况永远覆盖得到，只是不必每 3 小时问一次。
        """
        recent = self._is_recent_release(release_date)
        if satisfied:
            # 已经拿到足量弹幕：新番弹幕还会涨，老内容基本不会再变
            hours = self._backoff_ok_recent_hours if recent else self._backoff_cap_hours
        else:
            base = self._backoff_base_hours.get(verdict, 6)
            hours = base * (2 ** max(0, attempts - 1))
            hours = min(hours, self._backoff_cap_recent_hours if recent
                        else self._backoff_cap_hours)
        return (datetime.now() + timedelta(hours=hours)).isoformat(timespec="seconds")

    def _is_due(self, entry: Optional[Dict[str, Any]]) -> bool:
        """
        该文件是否到了该处理的时候。
        没有状态（从没刮过）、退避到期、或者产出 .ass 时的配置已经变了，都算到期。
        """
        if not entry:
            return True
        if entry.get("render") and entry["render"] != self._render_signature():
            return True
        next_check = entry.get("next_check")
        if not next_check:
            return True
        try:
            return datetime.now() >= datetime.fromisoformat(next_check)
        except (TypeError, ValueError):
            return True

    def _needs_retry(self, entry: Dict[str, Any]) -> bool:
        """该条目是否仍需复查"""
        if not self._enable_retry_task:
            return False
        if entry.get("verdict") == "ok" and \
                int(entry.get("danmu_count", 0)) >= self._min_danmu_count:
            return False
        return self._is_due(entry)

    def _record_scrape_state(self, file_path: str, result: generator.DanmuResult,
                             release_date: Optional[str] = None):
        """
        记录一次刮削结果。
        :param result: generator 返回的结果分类
        :param release_date: 媒体发布日期，供后续按新番/老番决定复查频率
        """
        norm = self._normalize_path(file_path) or file_path
        satisfied = result.is_ok and result.danmu_count >= self._min_danmu_count
        now = datetime.now().isoformat(timespec="seconds")
        with self._state_lock:
            entry = dict(self._scrape_state.get(norm) or {})
            if satisfied:
                attempts = 0
            else:
                # 只增不重置：它是退避的指数，不再是「重试几次就放弃」的计数
                attempts = int(entry.get("attempts", 0)) + 1
            effective_release = release_date or entry.get("release_date")
            entry.update({
                "verdict": result.outcome,
                "comment_id": result.comment_id or entry.get("comment_id"),
                "danmu_count": result.danmu_count,
                "attempts": attempts,
                "last_attempt": now,
                "release_date": effective_release,
                "next_check": self._compute_next_check(
                    result.outcome, attempts, satisfied, effective_release),
            })
            if satisfied:
                entry["last_success"] = now
                entry["render"] = self._render_signature()
            self._scrape_state[norm] = entry
        self._flush_scrape_state()

    # ------------------------------------------------------------------
    # 系列级缓存
    #
    # 「弹弹play 有没有这部剧」是剧的属性，不是集的属性。整季查询一次就能
    # 得到权威答案，缓存之后该剧所有文件都不必再打识别请求——178 集的剧
    # 从 178 次问变成 1 次。空结果同样缓存（确认无收录），但有 TTL，
    # 以便「老片后来被收录」仍能覆盖到。
    # ------------------------------------------------------------------

    @staticmethod
    def _series_key(tmdb_id: Any, tmdb_id_type: int) -> str:
        return f"{tmdb_id}:{tmdb_id_type}"

    def _series_ttl_hours(self, release_date: Optional[str], found: bool) -> int:
        """新番弹幕与条目都还在变，复查勤一些；完结老番隔很久看一次就够"""
        if self._is_recent_release(release_date):
            return self._series_ttl_recent_hours
        return self._series_ttl_hours_default if found else self._series_ttl_absent_hours

    @staticmethod
    def _is_recent_release(release_date: Optional[str]) -> bool:
        if not release_date:
            return False
        try:
            return (datetime.now() - datetime.strptime(release_date, '%Y-%m-%d')).days < 90
        except (TypeError, ValueError):
            return False

    def _get_series(self, tmdb_id: Any, tmdb_id_type: int,
                    release_date: Optional[str]) -> Optional["generator.SeriesLookup"]:
        """
        取该作品的整季结果，命中缓存则零请求。
        :return: SeriesLookup；None 表示这次什么都没问出来（不缓存）
        """
        if tmdb_id is None:
            return None
        key = self._series_key(tmdb_id, tmdb_id_type)
        with self._state_lock:
            cached = self._series_cache.get(key)
        if cached:
            fetched_at = cached.get("fetched_at")
            ttl = cached.get("ttl_hours", self._series_ttl_hours_default)
            try:
                age = datetime.now() - datetime.fromisoformat(fetched_at)
                if age.total_seconds() < ttl * 3600:
                    return generator.SeriesLookup(
                        cached.get("status", "ok"), cached.get("series") or []
                    )
            except (TypeError, ValueError):
                pass

        lookup = generator.DanmuAPI.search_series(tmdb_id, tmdb_id_type)
        if lookup.status == "unknown":
            # 什么都没问出来：不写缓存，否则会把一次网络抖动固化成「无收录」
            return None
        # truncated 也必须缓存：长番每个文件都重问一次整季，比不用整季查询还差
        with self._state_lock:
            self._series_cache[key] = {
                "status": lookup.status,
                "series": lookup.entries,
                "fetched_at": datetime.now().isoformat(timespec="seconds"),
                "ttl_hours": self._series_ttl_hours(release_date, lookup.usable),
            }
        if lookup.status == "absent":
            logger.info(f"弹弹play 未收录该作品（tmdb={tmdb_id}），已记入系列级缓存")
        elif lookup.status == "ok":
            total = sum(len(e.get("episodes") or []) for e in lookup.entries)
            logger.info(f"整季查询命中（tmdb={tmdb_id}）：{len(lookup.entries)} 个条目，共 {total} 集")
        self._flush_series_cache()
        return lookup

    def _load_series_cache(self):
        stored = self.get_data(self._series_cache_key)
        with self._state_lock:
            self._series_cache = stored if isinstance(stored, dict) else {}
        if self._series_cache:
            logger.info(f"加载了 {len(self._series_cache)} 条系列级缓存")

    def _flush_series_cache(self, force: bool = False):
        """与状态库同样的合并写盘策略"""
        try:
            if not force:
                with self._state_lock:
                    if self._state_save_deferred:
                        self._series_save_pending = True
                        return
            with self._state_lock:
                snapshot = copy.deepcopy(self._series_cache)
            self.save_data(self._series_cache_key, snapshot)
        except Exception as e:
            logger.error(f"保存系列级缓存失败: {e}")

    # 用一个哨兵区分「整季查询确认无收录」和「整季查询帮不上忙，走兜底」
    _SERIES_ABSENT = "__series_absent__"

    def _locate_via_series(self, tmdb_id: Any, tmdb_id_type: int, season: Optional[int],
                           episode: Optional[int], release_date: Optional[str],
                           file_path: str) -> Optional[str]:
        """
        用整季结果定位这一集。
        :return: 弹幕ID；_SERIES_ABSENT 表示整部确认无收录；
                 None 表示整季查询解决不了，交给 /match 兜底
        """
        if tmdb_id is None:
            return None
        try:
            lookup = self._get_series(tmdb_id, tmdb_id_type, release_date)
        except generator.DanmuThrottled:
            raise
        if lookup is None:
            return None

        if lookup.status == "truncated":
            # 结果被截断，条目和集数一起丢了。此时任何按序号的推导都可能
            # 静默错位几百集，只能整批作废交给逐集匹配
            return None

        if lookup.status == "absent":
            if tmdb_id_type == 1:
                # 该接口对电影的覆盖不完整（服务端实测有电影在这里查不到、
                # 却能从 bangumi 侧查到），所以电影的空结果不足以下「无收录」的
                # 结论，交给 /match 用文件哈希再兜一次
                logger.info(f"电影在整季接口无结果，回退常规匹配: {os.path.basename(file_path)}")
                return None
            return self._SERIES_ABSENT

        if not lookup.usable:
            return None

        comment_id = generator.DanmuAPI.locate_episode(lookup.entries, season, episode)
        if comment_id:
            logger.info(f"整季结果命中，零请求定位: {comment_id}")
            return comment_id
        # 剧是有的，但这一集不在权威列表里——大概率是本地集号识别有问题，
        # 交给 /match 用文件哈希兜一次，它不依赖集号
        logger.info(
            f"整季列表中没有 S{season}E{episode}，回退常规匹配: {os.path.basename(file_path)}"
        )
        return None

    def _forget_scrape_state(self, file_path: str) -> bool:
        """删除某个文件的刮削状态（文件已不存在、或确认无需再复查）"""
        norm = self._normalize_path(file_path) or file_path
        with self._state_lock:
            removed = self._scrape_state.pop(norm, None) is not None
        if removed:
            self._flush_scrape_state()
        return removed

    def _retry_candidates(self) -> List[Tuple[str, Dict[str, Any]]]:
        """当前仍需复查的条目"""
        with self._state_lock:
            return [(path, dict(entry)) for path, entry in self._scrape_state.items()
                    if self._needs_retry(entry)]

    def update_path(self, path: str) -> schemas.Response:
        """
        更新刮削路径
        """
        if path is None:
            return schemas.Response(success=False, message="缺少路径参数")
        try:
            self._path = path
            self._persist_config()
            logger.info(f"更新路径: {self._path}")
            return schemas.Response(success=True, message="路径已更新", data={"path": self._path})
        except Exception as e:
            logger.error(f"更新路径失败: {e}")
            return schemas.Response(success=False, message=f"更新路径失败: {str(e)}")

    def _collect_media_files(self, path: str) -> List[str]:
        """
        收集路径下所有支持的媒体文件（目录则递归）
        """
        collected = []
        if os.path.isfile(path):
            if self._is_supported_file(path):
                collected.append(path)
            return collected
        for root, _, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                if self._is_supported_file(file_path):
                    collected.append(file_path)
        return collected

    def _filter_due(self, files: List[str], force: bool) -> Tuple[List[str], int]:
        """
        按退避计划筛掉还没到复查时间的文件。
        这是请求量真正降下来的地方：确认无收录的老内容不再每 3 小时问一遍。
        :param force: 用户显式要求重刮时跳过筛选
        :return: (待处理文件, 被跳过数量)
        """
        if force:
            return files, 0
        due = []
        for file_path in files:
            norm = self._normalize_path(file_path) or file_path
            with self._state_lock:
                entry = self._scrape_state.get(norm)
            if self._is_due(entry):
                due.append(file_path)
        return due, len(files) - len(due)

    def _start_scrape_batch(self, files: List[str], label: str) -> bool:
        """
        启动后台批量刮削，已有任务运行时返回False
        """
        if self._stop_event.is_set():
            logger.warning("插件正在停止，拒绝启动批量刮削")
            return False
        with self._scrape_lock:
            if self._scrape_progress.get("running"):
                return False
            self._scrape_progress = {
                "running": True,
                "total": len(files),
                "processed": 0,
                "success": 0,
                "failed": 0,
                "absent": 0,
                "empty": 0,
                "deferred": 0,
                "skipped": 0,
                "current_file": None,
                "started_at": time.time(),
                "duration": 0
            }
        thread = threading.Thread(
            target=self._run_scrape_batch,
            args=(files, label),
            daemon=True
        )
        self._scrape_thread = thread
        thread.start()
        return True

    def _scrape_file(self, file_path: str) -> str:
        """
        刮削单个文件并归类结果
        :return: ok（生成成功）/ absent（弹弹play 未收录，不是失败）/
                 empty（已收录但暂无弹幕）/ failed（真失败，值得重试）/
                 deferred（被服务端限流，稍后重试）/ skipped（重试也不会改变结果）
        """
        try:
            return self.generate_danmu(file_path).outcome
        except generator.DanmuThrottled as e:
            # 被限流不是失败：既不计入重试次数，也不该判定为「没有弹幕」
            logger.warning(f"刮削被限流，本次跳过: {file_path}: {e}")
            return "deferred"
        except generator.DanmuUnresolvable as e:
            logger.warning(f"跳过无法判定的文件: {e}")
            return "skipped"
        except Exception as e:
            logger.error(f"刮削文件失败: {file_path}: {e}")
            return "failed"

    def _scrape_one(self, file_path: str):
        outcome = self._scrape_file(file_path)
        with self._scrape_lock:
            self._scrape_progress["processed"] += 1
            if outcome == "ok":
                self._scrape_progress["success"] += 1
            elif outcome in ("absent", "empty"):
                self._scrape_progress[outcome] += 1
            elif outcome == "deferred":
                self._scrape_progress["deferred"] += 1
            elif outcome == "skipped":
                self._scrape_progress["skipped"] += 1
            else:
                self._scrape_progress["failed"] += 1

    def _run_scrape_batch(self, files: List[str], label: str):
        logger.info(f"开始批量刮削（{label}），共 {len(files)} 个文件")
        # 批量期间不逐文件回写配置，结束后统一保存一次重试任务
        with self._state_lock:
            self._state_save_deferred = True
            self._state_save_pending = False
            self._series_save_pending = False
        threading_list = []
        stopped = False
        try:
            for file_path in files:
                if self._stop_event.is_set():
                    stopped = True
                    logger.info(f"收到停止信号，中止批量刮削（{label}）")
                    break
                # 闸门长时间关闭说明服务端配额已耗尽，继续排队没有意义，
                # 留给下次调度即可；短暂限流由请求层就地等待处理
                blocked = generator.DanmuAPI.blocked_seconds()
                if blocked > generator.DanmuAPI.GATE_WAIT_MAX:
                    stopped = True
                    logger.warning(
                        f"弹弹API限流中（约 {blocked / 60:.0f} 分钟），"
                        f"中止批量刮削（{label}），剩余文件留待下次执行"
                    )
                    break
                with self._scrape_lock:
                    self._scrape_progress["current_file"] = os.path.basename(file_path)
                if len(threading_list) >= self._max_threads:
                    threading_list[0].join()
                    threading_list.pop(0)
                thread = threading.Thread(
                    target=self._scrape_one,
                    args=(file_path,),
                    daemon=True
                )
                thread.start()
                threading_list.append(thread)
            for thread in threading_list:
                thread.join()
        finally:
            with self._scrape_lock:
                started_at = self._scrape_progress.get("started_at")
                if started_at:
                    self._scrape_progress["duration"] = int(time.time() - started_at)
                self._scrape_progress["running"] = False
                self._scrape_progress["current_file"] = None
                summary = dict(self._scrape_progress)
            with self._state_lock:
                self._state_save_deferred = False
                state_save_pending = self._state_save_pending
                series_save_pending = self._series_save_pending
                self._state_save_pending = False
                self._series_save_pending = False
            if state_save_pending:
                self._flush_scrape_state()
            if series_save_pending:
                self._flush_series_cache()
        logger.info(
            f"批量刮削{'中止' if stopped else '完成'}（{label}）：成功 {summary['success']}，"
            f"无收录 {summary['absent']}，暂无弹幕 {summary['empty']}，"
            f"失败 {summary['failed']}，限流跳过 {summary['deferred']}，"
            f"无法判定 {summary['skipped']}，共 {summary['total']}"
        )

    def scrape_directory(self, directory_path: str = None, force: bool = False) -> schemas.Response:
        """
        刮削指定目录下所有媒体文件
        """
        if not directory_path:
            return schemas.Response(success=False, message="缺少目录路径")
        directory_path = self._resolve_in_roots(directory_path)
        if not directory_path:
            return schemas.Response(success=False, message="路径不在配置的刮削范围内")
        if not os.path.isdir(directory_path):
            return schemas.Response(success=False, message="目录不存在")
        files = self._collect_media_files(directory_path)
        if not files:
            return schemas.Response(success=False, message="目录下没有支持的媒体文件")
        files, skipped = self._filter_due(files, force)
        if not files:
            return schemas.Response(
                success=True,
                message=f"{skipped} 个文件都还没到复查时间，本次无需刮削",
                data={"total": 0, "skipped": skipped}
            )
        if not self._start_scrape_batch(files, f"目录 {directory_path}"):
            return schemas.Response(success=False, message="已有刮削任务进行中，请稍后再试")
        message = f"已开始刮削，共 {len(files)} 个文件"
        if skipped:
            message += f"（{skipped} 个未到复查时间已跳过）"
        return schemas.Response(
            success=True, message=message,
            data={"total": len(files), "skipped": skipped}
        )

    def generate_danmu_global(self, force: bool = False):
        """
        全局刮削弹幕
        """
        if not self._path:
            logger.warning("未设置刮削路径，跳过刮削")
            return schemas.Response(success=False, message="没有设定路径")

        logger.info("开始弹幕刮削")
        paths = self._configured_roots()

        files = []
        for path in paths:
            if not os.path.exists(path):
                logger.warning(f"路径不存在: {path}")
                return schemas.Response(success=False, message=f"路径不存在: {path}")
            files.extend(self._collect_media_files(path))

        if not files:
            return schemas.Response(success=False, message="未找到支持的媒体文件")
        files, skipped = self._filter_due(files, force)
        if not files:
            return schemas.Response(
                success=True,
                message=f"{skipped} 个文件都还没到复查时间，本次无需刮削",
                data={"total": 0, "skipped": skipped}
            )
        if not self._start_scrape_batch(files, "全局"):
            return schemas.Response(success=False, message="已有刮削任务进行中")
        message = f"已开始刮削，共 {len(files)} 个文件"
        if skipped:
            message += f"（{skipped} 个未到复查时间已跳过）"
        return schemas.Response(
            success=True, message=message,
            data={"total": len(files), "skipped": skipped}
        )
    
    @eventmanager.register(EventType.TransferComplete)
    def generate_danmu_after_transfer(self, event):
        """
        传输完成后生成弹幕
        """
        if not self._enabled or not self._auto_scrape:
            return

        def __to_dict(_event):
            """
            递归将对象转换为字典
            """
            if isinstance(_event, dict):
                return {k: __to_dict(v) for k, v in _event.items()}
            elif isinstance(_event, list):
                return [__to_dict(item) for item in _event]
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

        try:
            raw_data = __to_dict(event.event_data)
            target_file = raw_data.get("transferinfo", {}).get("file_list_new", [None])[0]
            
            if not target_file:
                logger.warning("未找到目标文件")
                return

            logger.info(f"开始生成弹幕文件：{target_file}")
            # 用 _scrape_file 而非 generate_danmu：限流会抛异常，
            # 裸线程里会变成一条无人处理的堆栈
            thread = threading.Thread(
                target=self._scrape_file,
                args=(target_file,),
                daemon=True
            )
            thread.start()
        except Exception as e:
            logger.error(f"处理传输完成事件失败: {e}")

    def stop_service(self):
        """
        退出插件：通知批量刮削与重试任务停止，并等待当前批次收尾
        """
        self._stop_event.set()
        thread = self._scrape_thread
        if thread and thread.is_alive():
            logger.info("等待批量刮削任务退出...")
            thread.join(timeout=self._stop_wait_seconds)
            if thread.is_alive():
                logger.warning(f"批量刮削任务未在{self._stop_wait_seconds}秒内退出，插件继续停止")
        self._scrape_thread = None

    def _count_danmu_lines_cached(self, ass_file: str, stat_result: Optional[os.stat_result] = None) -> int:
        """
        带缓存的弹幕数量统计，文件未变化时直接返回缓存值，避免重复整文件读取
        :param ass_file: 弹幕文件路径
        :param stat_result: 已有的stat结果（来自os.scandir时避免重复stat）
        :return: 弹幕数量
        """
        try:
            st = stat_result or os.stat(ass_file)
        except OSError:
            return 0
        cached = self._danmu_count_cache.get(ass_file)
        if cached and cached[0] == st.st_mtime_ns and cached[1] == st.st_size:
            return cached[2]
        count = self.count_danmu_lines(ass_file)
        self._danmu_count_cache[ass_file] = (st.st_mtime_ns, st.st_size, count)
        return count

    def count_danmu_lines(self, ass_file: str) -> int:
        """
        计算弹幕文件中的弹幕数量
        :param ass_file: 弹幕文件路径
        :return: 弹幕数量
        """
        try:
            if not os.path.exists(ass_file):
                return 0
            count = 0
            with open(ass_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('Dialogue:'):
                        count += 1
            return count
        except Exception as e:
            logger.error(f"计算弹幕数量失败: {e}")
            return 0

    def scan_path(self, path: str = None, current_dir: str = None) -> schemas.Response:
        """
        扫描路径下的媒体文件和弹幕信息
        :param path: 配置的根路径
        :param current_dir: 当前浏览的目录（用于点击式导航）
        :return: 目录结构信息
        """
        logger.debug(f"开始扫描路径: {path if path else self._path}, 当前目录: {current_dir}")
        
        # 如果有current_dir，直接扫描该目录
        if current_dir:
            return self.scan_subfolder(current_dir)
        
        # 否则使用配置的路径
        if not path:
            path = self._path
            
        if not path:
            logger.debug("未设置扫描路径，返回错误")
            return schemas.Response(success=False, message="未配置刮削路径")
        
        # 处理多路径情况；传入的路径同样限制在配置的根路径内
        paths = []
        for raw in path.split('\n'):
            if not raw.strip():
                continue
            resolved = self._resolve_in_roots(raw.strip())
            if not resolved:
                return schemas.Response(success=False, message="路径不在配置的刮削范围内")
            paths.append(resolved)
        logger.debug(f"解析到 {len(paths)} 个有效路径")

        if len(paths) > 1:
            # 多路径情况，返回多个根目录
            logger.debug("处理多路径情况")
            result = {
                "name": "根目录",
                "path": "",
                "type": "root",
                "is_root": True,
                "children": []
            }
            
            for single_path in paths:
                logger.debug(f"处理子路径: {single_path}")
                if os.path.exists(single_path):
                    child_result = self._scan_current_directory(single_path)
                    result["children"].append(child_result)
                else:
                    logger.warning(f"路径不存在: {single_path}")
                    
            logger.debug(f"多路径扫描完成，共 {len(result['children'])} 个有效路径")
            return schemas.Response(success=True, data=result)
        elif len(paths) == 1:
            # 单路径情况
            single_path = paths[0]
            logger.debug(f"处理单路径: {single_path}")
            if not os.path.exists(single_path):
                logger.warning(f"路径不存在: {single_path}")
                return schemas.Response(success=False, message=f"路径不存在: {single_path}")
            
            result = self._scan_current_directory(single_path, is_root=True)
            logger.debug("单路径扫描完成")
            return schemas.Response(success=True, data=result)
        else:
            logger.debug("没有提供有效路径")
            return schemas.Response(success=False, message="未提供有效路径")

    def _scan_current_directory(self, path: str, is_root: bool = False) -> Dict[str, Any]:
        """
        扫描当前目录的直接内容（不递归）
        :param path: 要扫描的目录路径
        :param is_root: 是否为根目录
        :return: 目录结构信息
        """
        logger.debug(f"开始扫描当前目录: {path}, 是否为根目录: {is_root}")
        result = {
            "name": os.path.basename(path) or path,
            "path": path,
            "type": "directory",
            "is_root": is_root,
            "children": []
        }
        if os.path.isdir(path):
            manual_dir_match = self._get_manual_match(path, check_legacy=False)
            result["manual_match"] = manual_dir_match
            result["manual_scope"] = manual_dir_match.get("scope") if manual_dir_match else None
            result["directory_path"] = path
        else:
            manual_file_match = self._get_manual_file_match(path)
            if manual_file_match:
                result["manual_match"] = manual_file_match
                result["manual_scope"] = manual_file_match.get("scope")
            else:
                parent_manual = self._get_manual_match(os.path.dirname(path), check_legacy=False)
                result["manual_match"] = parent_manual
                result["manual_scope"] = parent_manual.get("scope") if parent_manual else None
            result["directory_path"] = os.path.dirname(path)

        try:
            # 如果是文件，直接返回文件信息
            if os.path.isfile(path):
                logger.debug(f"{path} 是文件")
                if self._is_supported_file(path):
                    logger.debug(f"{path} 是媒体文件")
                    result["type"] = "media"
                    result["manual_match"] = self._get_manual_match(os.path.dirname(path), check_legacy=False)
                    # 检查是否存在对应的弹幕文件
                    ass_file = f"{os.path.splitext(path)[0]}.danmu.ass"
                    result["danmu_count"] = self._count_danmu_lines_cached(ass_file)
                return result

            # 扫描目录的直接子项
            logger.debug(f"{path} 是目录，开始扫描直接子项")

            try:
                # 单次scandir同时拿到名称和类型，避免每个条目重复stat
                with os.scandir(path) as it:
                    # 跳过隐藏文件和系统文件
                    entries = [e for e in it if not e.name.startswith('.')]
                logger.debug(f"{path} 目录中共有 {len(entries)} 个项目")
            except PermissionError:
                logger.warning(f"无权限访问目录: {path}")
                result["error"] = "无权限访问该目录"
                return result
            except Exception as e:
                logger.warning(f"列出目录内容失败: {path}, 错误: {str(e)}")
                result["error"] = f"列出目录内容失败: {str(e)}"
                return result

            # 先处理目录，再处理文件
            entry_map = {e.name: e for e in entries}
            directories = []
            files = []

            for entry in entries:
                try:
                    if entry.is_dir():
                        directories.append(entry)
                    elif entry.is_file() and self._is_supported_file(entry.path):
                        files.append(entry)
                except OSError:
                    continue

            # 子文件的目录级手动匹配就是当前目录的匹配，直接复用，不再逐文件查询
            current_dir_manual = result.get("manual_match")
            current_dir_scope = result.get("manual_scope")

            # 添加目录到结果
            for entry in sorted(directories, key=lambda e: e.name):
                child = {
                    "name": entry.name,
                    "path": entry.path,
                    "type": "directory",
                    "children": []
                }
                manual_dir_match = self._get_manual_match(entry.path, check_legacy=False)
                child["manual_match"] = manual_dir_match
                child["manual_scope"] = manual_dir_match.get("scope") if manual_dir_match else None
                child["directory_path"] = entry.path
                result["children"].append(child)

            # 添加媒体文件到结果
            for entry in sorted(files, key=lambda e: e.name):
                child = {
                    "name": entry.name,
                    "path": entry.path,
                    "type": "media",
                    "children": []
                }
                file_manual = self._get_manual_file_match(entry.path)
                if file_manual:
                    child["manual_match"] = file_manual
                    child["manual_scope"] = file_manual.get("scope")
                else:
                    child["manual_match"] = current_dir_manual
                    child["manual_scope"] = current_dir_scope
                child["directory_path"] = path
                # 弹幕文件与媒体同目录，用本次scandir结果判断存在性，避免逐文件stat
                ass_name = f"{os.path.splitext(entry.name)[0]}.danmu.ass"
                ass_entry = entry_map.get(ass_name)
                if ass_entry is not None:
                    try:
                        child["danmu_count"] = self._count_danmu_lines_cached(ass_entry.path, ass_entry.stat())
                    except OSError:
                        child["danmu_count"] = 0
                else:
                    child["danmu_count"] = 0
                result["children"].append(child)

            logger.debug(f"目录 {path} 扫描完成，发现 {len(files)} 个媒体文件，{len(directories)} 个子目录")
            return result
        except Exception as e:
            logger.error(f"扫描路径失败: {path}, 错误: {e}")
            # 出错时返回基本信息，不中断整个扫描
            result["error"] = str(e)
            return result

    def generate_danmu_single(self, file_path: str) -> schemas.Response:
        """
        为单个文件生成弹幕
        :param file_path: 媒体文件路径
        :return: 生成结果
        """
        if not file_path:
            return schemas.Response(success=False, message="缺少文件路径")

        file_path = self._resolve_in_roots(file_path)
        if not file_path:
            return schemas.Response(success=False, message="路径不在配置的刮削范围内")

        if not os.path.exists(file_path):
            return schemas.Response(success=False, message="文件不存在")

        if not self._is_supported_file(file_path):
            if file_path.endswith('.strm') and not self._enable_strm:
                return schemas.Response(success=False, message=".strm文件刮削功能未启用")
            else:
                return schemas.Response(success=False, message="不支持的文件格式")
            
        try:
            result = self.generate_danmu(file_path)
            # outcome 一并返回，前端据此区分「成功 / 无收录 / 暂无弹幕 / 失败」。
            # absent 与 empty 不是错误——把它们报成失败会让用户去做
            # 重扫、手动匹配这些不可能奏效的操作
            data = {
                "outcome": result.outcome,
                "danmu_count": result.danmu_count,
                "file_path": file_path
            }
            if result.is_ok:
                logger.info(f"生成弹幕成功，弹幕数量: {result.danmu_count}")
                return schemas.Response(success=True, message="弹幕生成成功", data=data)
            if result.outcome == "failed":
                return schemas.Response(success=False, message=result.message, data=data)
            return schemas.Response(success=True, message=result.message, data=data)
        except generator.DanmuThrottled as e:
            logger.warning(f"生成弹幕被限流: {file_path}: {e}")
            return schemas.Response(success=False, message=str(e))
        except generator.DanmuUnresolvable as e:
            logger.warning(f"无法判定弹幕归属: {e}")
            return schemas.Response(success=False, message=e.reason)
        except Exception as e:
            logger.error(f"生成弹幕失败: {e}")
            return schemas.Response(success=False, message=f"生成弹幕失败: {str(e)}")

    def search_anime(self, keyword: Optional[str] = None, type: Optional[str] = None) -> schemas.Response:
        """
        搜索弹弹动漫
        """
        keyword = keyword.strip() if keyword else ""
        if not keyword:
            return schemas.Response(success=False, message="搜索关键字不能为空")

        try:
            # UI请求不能挂在限速队列里等，取不到令牌就直接告诉用户稍后再试
            data = generator.DanmuAPI.search_anime(
                keyword, type, acquire_timeout=self._ui_acquire_timeout
            )
            if not data.get("success", False):
                message = data.get("errorMessage") or "搜索失败"
                logger.warning(f"弹弹搜索返回失败: {message}")
                return schemas.Response(success=False, message=message, data=data)

            return schemas.Response(success=True, data=data)
        except generator.DanmuThrottled as e:
            logger.warning(f"搜索弹弹被限流: {e}")
            return schemas.Response(success=False, message=str(e))
        except Exception as e:
            logger.error(f"搜索弹弹动漫失败: {e}")
            return schemas.Response(success=False, message=f"搜索失败: {str(e)}")

    def set_manual_match(self, data: Dict[str, Any]) -> schemas.Response:
        """
        保存手动匹配结果
        """
        if not isinstance(data, dict):
            return schemas.Response(success=False, message="请求数据无效")

        file_path = data.get("file_path")
        directory_path = data.get("directory")
        scope = (data.get("scope") or "").lower()
        anime = data.get("anime") or {}

        if scope not in {"file", "directory"}:
            scope = "directory" if directory_path or (file_path and data.get("directory")) else "file"

        if scope == "file":
            if not file_path:
                return schemas.Response(success=False, message="缺少文件路径")
            file_path = self._resolve_in_roots(file_path)
            if not file_path:
                return schemas.Response(success=False, message="路径不在配置的刮削范围内")
        manual_dir = self._resolve_manual_directory(file_path=file_path, directory_path=directory_path)
        if scope == "directory":
            if not manual_dir:
                return schemas.Response(success=False, message="无法确定手动匹配目录")
            # 目录匹配会向该目录写入 .dandan.anime.json，必须限制在配置范围内
            manual_dir = self._resolve_in_roots(manual_dir)
            if not manual_dir:
                return schemas.Response(success=False, message="路径不在配置的刮削范围内")
            if not os.path.isdir(manual_dir):
                return schemas.Response(success=False, message="匹配目录不存在，请刷新后重试")

        anime_id = anime.get("animeId") or anime.get("anime_id")
        if anime_id is None:
            return schemas.Response(success=False, message="缺少animeId")

        try:
            anime_id = int(anime_id)
        except (TypeError, ValueError):
            return schemas.Response(success=False, message="animeId格式无效")

        episode_offset = data.get("episodeOffset", data.get("episode_offset"))
        if episode_offset in (None, ""):
            episode_offset = 0
        try:
            episode_offset = int(episode_offset)
        except (TypeError, ValueError):
            return schemas.Response(success=False, message="集数偏移必须为整数")

        manual_info = {
            "animeId": anime_id,
            "animeTitle": anime.get("animeTitle"),
            "imageUrl": anime.get("imageUrl"),
            "type": anime.get("type"),
            "typeDescription": anime.get("typeDescription"),
            "episodeCount": anime.get("episodeCount"),
            "rating": anime.get("rating"),
            "startDate": anime.get("startDate"),
            "source": "manual_file" if scope == "file" else "manual",
            "updatedAt": datetime.now().isoformat(timespec="seconds")
        }
        if episode_offset:
            manual_info["episodeOffset"] = episode_offset

        try:
            if scope == "file":
                manual_info["scope"] = "file"
                self._update_manual_file_match_cache(file_path, manual_info)
                logger.info(f"单文件手动匹配已保存: {file_path} -> {anime_id}")
            else:
                manual_info["scope"] = "directory"
                self._write_manual_match_file(manual_dir, manual_info)
                self._update_manual_match_cache(manual_dir, manual_info)
                logger.info(f"目录手动匹配已保存: {manual_dir} -> {anime_id}")
            return schemas.Response(
                success=True,
                message="手动匹配已保存",
                data={
                    "directory": manual_dir if scope == "directory" else self._resolve_manual_directory(file_path=file_path),
                    "file_path": file_path if scope == "file" else None,
                    "manual_match": manual_info
                }
            )
        except Exception as e:
            logger.error(f"保存手动匹配失败: {e}")
            return schemas.Response(success=False, message=f"保存失败: {str(e)}")

    def remove_manual_match(self, file_path: Optional[str] = None, directory: Optional[str] = None,
                             scope: Optional[str] = None) -> schemas.Response:
        """
        移除手动匹配
        """
        scope = (scope or "").lower()
        if scope not in {"file", "directory"}:
            scope = "file" if file_path and not directory else "directory"

        if scope == "file":
            norm = self._normalize_path(file_path)
            if not norm:
                return schemas.Response(success=False, message="未提供有效文件路径")
            removed = self._manual_file_matches.pop(norm, None)
            if removed:
                self._save_manual_state()
            return schemas.Response(success=True, message="单文件手动匹配已移除", data={"file_path": file_path})

        manual_dir = self._resolve_manual_directory(file_path=file_path, directory_path=directory)
        if not manual_dir:
            return schemas.Response(success=False, message="未提供有效目录")

        # 该接口会删除目录下的 .dandan.anime.json，必须限制在配置范围内
        manual_dir = self._resolve_in_roots(manual_dir)
        if not manual_dir:
            return schemas.Response(success=False, message="路径不在配置的刮削范围内")

        json_path = self._manual_json_path(manual_dir)
        try:
            if os.path.exists(json_path):
                os.remove(json_path)
                logger.info(f"已删除手动匹配文件: {json_path}")
        except Exception as e:
            logger.warning(f"删除手动匹配文件失败: {e}")

        self._update_manual_match_cache(manual_dir, None)
        return schemas.Response(success=True, message="目录手动匹配已移除", data={"directory": manual_dir})

    def scan_subfolder(self, subfolder_path: str = None) -> schemas.Response:
        """
        专门用于扫描子文件夹的内容（点击式导航）
        :param subfolder_path: 子文件夹路径
        :return: 该子文件夹的内容
        """
        logger.debug(f"扫描子文件夹: {subfolder_path}")
        
        if not subfolder_path:
            logger.warning("未提供子文件夹路径")
            return schemas.Response(success=False, message="未提供子文件夹路径")

        subfolder_path = self._resolve_in_roots(subfolder_path)
        if not subfolder_path:
            return schemas.Response(success=False, message="路径不在配置的刮削范围内")

        if not os.path.exists(subfolder_path):
            logger.warning(f"子文件夹不存在: {subfolder_path}")
            return schemas.Response(success=False, message="文件夹不存在")

        if not os.path.isdir(subfolder_path):
            logger.warning(f"指定路径不是文件夹: {subfolder_path}")
            return schemas.Response(success=False, message="指定路径不是文件夹")

        try:
            # 检查当前路径是否为用户配置的根路径之一
            is_root = subfolder_path in self._configured_roots()

            # 直接扫描这个子文件夹的内容
            result = self._scan_current_directory(subfolder_path, is_root=is_root)
            logger.debug("子文件夹扫描完成")
            return schemas.Response(success=True, data=result)
        except Exception as e:
            logger.error(f"扫描子文件夹失败: {subfolder_path}, 错误: {e}")
            return schemas.Response(success=False, message=f"扫描子文件夹失败: {str(e)}")

    def get_retry_tasks(self) -> Dict[str, Any]:
        """
        获取重试任务列表
        :return: 重试任务列表
        """
        display_tasks = {}
        for file_path, entry in self._retry_candidates():
            display_tasks[file_path] = {
                "retry_count": entry.get("attempts", 0),
                "last_attempt": entry.get("last_attempt"),
                "file_path": file_path,
                "last_danmu_count": entry.get("danmu_count", 0),
                "verdict": entry.get("verdict"),
            }

        return schemas.Response(
            success=True,
            message=f"获取到 {len(display_tasks)} 个重试任务",
            data={
                "tasks": display_tasks,
                "total": len(display_tasks),
                "min_danmu_count": self._min_danmu_count
            }
        )

    def process_retry_tasks(self) -> Dict[str, Any]:
        """
        处理重试任务
        :return: 处理结果
        """
        tasks_to_process = self._retry_candidates()
        if not tasks_to_process:
            return schemas.Response(success=True, message="没有待处理的重试任务")

        logger.info(f"开始处理 {len(tasks_to_process)} 个重试任务")
        processed_count = 0
        success_count = 0
        failed_count = 0
        removed_count = 0

        deferred_count = 0
        absent_count = 0
        for file_path, task_info in tasks_to_process:
            if self._stop_event.is_set():
                logger.info("收到停止信号，中止重试任务处理")
                break

            # 闸门长时间关闭时停止本轮，剩余任务留到下次定时执行
            blocked = generator.DanmuAPI.blocked_seconds()
            if blocked > generator.DanmuAPI.GATE_WAIT_MAX:
                logger.warning(
                    f"弹弹API限流中（约 {blocked / 60:.0f} 分钟），中止本轮重试任务"
                )
                break

            # 检查文件是否仍然存在
            if not os.path.exists(file_path):
                logger.warning(f"重试任务文件不存在，移除: {file_path}")
                self._forget_scrape_state(file_path)
                removed_count += 1
                continue

            logger.info(f"处理重试任务: {file_path} (第 {task_info.get('attempts', 0) + 1} 次尝试)")
            
            try:
                # 生成弹幕（这会自动更新重试任务状态）
                result = self.generate_danmu(file_path)
                processed_count += 1
                
                # 检查结果
                if result.is_ok and result.danmu_count >= self._min_danmu_count:
                    success_count += 1
                    logger.info(f"重试成功: {file_path}，弹幕数量: {result.danmu_count}")
                elif result.outcome == "absent":
                    absent_count += 1
                    logger.info(f"弹弹play未收录，无需重试: {file_path}")
                else:
                    failed_count += 1
                    logger.info(f"重试未成功: {file_path}，{result.message or '弹幕数量仍不足'}")

            except generator.DanmuThrottled as e:
                # 不计入失败，重试次数也没有增加，下轮原样再来
                deferred_count += 1
                logger.warning(f"重试被限流，本轮跳过: {file_path}: {e}")
            except generator.DanmuUnresolvable as e:
                # 条件不变结果就不变，留在列表里只会每轮空转，直接移除
                self._forget_scrape_state(file_path)
                removed_count += 1
                logger.info(f"重试无法改变结果，从重试列表移除: {e}")
            except Exception as e:
                logger.error(f"处理重试任务失败: {file_path}，错误: {e}")
                failed_count += 1
        
        self._flush_scrape_state()
        
        result_message = (
            f"重试任务处理完成。处理: {processed_count}, 成功: {success_count}, "
            f"失败: {failed_count}, 无收录: {absent_count}, 限流跳过: {deferred_count}, "
            f"移除: {removed_count}, 剩余: {len(self._retry_candidates())}"
        )
        logger.info(result_message)

        return schemas.Response(
            success=True,
            message=result_message,
            data={
                "processed": processed_count,
                "success": success_count,
                "failed": failed_count,
                "absent": absent_count,
                "deferred": deferred_count,
                "removed": removed_count,
                "remaining": len(self._retry_candidates())
            }
        )

    def clear_retry_tasks(self) -> Dict[str, Any]:
        """
        清空重试任务
        :return: 清空结果
        """
        candidates = self._retry_candidates()
        task_count = len(candidates)
        for file_path, _ in candidates:
            with self._state_lock:
                self._scrape_state.pop(file_path, None)
        self._flush_scrape_state()
        
        logger.info(f"已清空 {task_count} 个重试任务")
        return schemas.Response(
            success=True,
            message=f"已清空 {task_count} 个重试任务"
        )

    def remove_retry_task(self, file_path: str) -> Dict[str, Any]:
        """
        移除重试任务
        :param file_path: 要移除的重试任务的文件路径
        :return: 移除结果
        """
        if not file_path:
            return schemas.Response(success=False, message="文件路径不能为空")
            
        removed = self._forget_scrape_state(file_path)
        if removed:
            logger.info(f"重试任务已移除: {file_path}")
            return schemas.Response(
                success=True,
                message=f"重试任务已移除: {file_path}"
            )
        else:
            return schemas.Response(
                success=False,
                message=f"未找到重试任务: {file_path}"
            )

    def auto_process_retry_tasks(self):
        """
        定时自动处理重试任务
        """
        try:
            if not self._enabled or not self._enable_retry_task:
                logger.debug("弹幕插件或重试任务功能未启用，跳过定时处理")
                return
                
            pending = len(self._retry_candidates())
            if not pending:
                logger.debug("没有待处理的重试任务")
                return

            logger.info(f"定时任务开始处理 {pending} 个重试任务")
            
            # 调用现有的处理重试任务方法
            result = self.process_retry_tasks()
            
            if result.success:
                logger.info(f"定时任务完成，{result.message}")
            else:
                logger.warning(f"定时任务处理失败: {result.message}")
                
        except Exception as e:
            logger.error(f"定时处理重试任务失败: {e}")
