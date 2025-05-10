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
from datetime import datetime

from typing import Any, List, Dict, Tuple, Optional
import subprocess
import os
import threading
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
    plugin_version = "1.3.0"
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
    
    media_chain = MediaChain()
    
    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled", False)
            self._width = config.get("width", 1920)
            self._height = config.get("height", 1080)
            # self._fontface = config.get("fontface")
            self._fontsize = config.get("fontsize", 50)
            self._alpha = config.get("alpha", 0.8)
            self._duration = config.get("duration", 15)
            self._path = config.get("path", "")
            self._onlyFromBili = config.get("onlyFromBili", False)
            self._useTmdbID = config.get("useTmdbID", True)
            self._auto_scrape = config.get("auto_scrape", False)
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
            "description": "扫描路径下的媒体文件和弹幕信息"
        },
        {
            "path": "/generate_danmu",
            "endpoint": self.generate_danmu_single,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "生成单个文件弹幕",
            "description": "为指定文件生成弹幕"
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
            "onlyFromBili": self._onlyFromBili,
            "useTmdbID": self._useTmdbID,
            "auto_scrape": self._auto_scrape
        }
        
    def _save_config(self, config: dict):
        """保存配置"""
        try:
            self._enabled = config.get("enabled", False)
            self._width = config.get("width", 1920)
            self._height = config.get("height", 1080)
            self._fontsize = config.get("fontsize", 50)
            self._alpha = config.get("alpha", 0.8)
            self._duration = config.get("duration", 15)
            self._path = config.get("path", "")
            self._onlyFromBili = config.get("onlyFromBili", False)
            self._useTmdbID = config.get("useTmdbID", True)
            self._auto_scrape = config.get("auto_scrape", False)
            
            # 保存到系统配置
            self.update_config({
                "enabled": self._enabled,
                "width": self._width,
                "height": self._height,
                "fontsize": self._fontsize,
                "alpha": self._alpha,
                "duration": self._duration,
                "path": self._path,
                "onlyFromBili": self._onlyFromBili,
                "useTmdbID": self._useTmdbID,
                "auto_scrape": self._auto_scrape
            })
            
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
        return {
            "enabled": self._enabled
        }

    def generate_danmu(self, file_path: str) -> Optional[str]:
        """
        生成弹幕文件
        :param file_path: 视频文件路径
        :return: 生成的弹幕文件路径，如果失败则返回None或失败原因字符串
        """
        meta = MetaInfo(file_path)
        tmdb_id = None
        episode = None
        release_date = None
        use_short_cache_ttl = False
        if self._useTmdbID:
            media_info = self.media_chain.recognize_media(meta=meta)
            if media_info:
                tmdb_id = media_info.tmdb_id
                episode = meta.episode.split('E')[1] if meta.episode else None
                release_date = media_info.release_date
                if release_date:
                    try:
                        release_datetime = datetime.strptime(release_date, '%Y-%m-%d')
                        is_recent = (datetime.now() - release_datetime).days < 90
                        if is_recent:
                            logger.info(f"媒体 {tmdb_id} 是最近90天内发布的内容,使用短缓存")
                            use_short_cache_ttl = True
                    except ValueError:
                        logger.warning(f"无效的发布日期格式: {release_date},使用默认缓存时间")
    
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
                60 if use_short_cache_ttl else None
            )
            # 如果返回字符串且包含弹幕数量为0，说明是失败原因
            if isinstance(result, str) and result.startswith('弹幕数量为0'):
                logger.info(result)
                return result
            return result
        except Exception as e:
            logger.error(f"生成弹幕失败: {e}")
            return f"生成弹幕失败: {str(e)}"

    def update_path(self, path: str):
        """
        更新路径
        """
        self._path = path
        logger.info(f"更新路径: {self._path}")
        
    def generate_danmu_global(self):
        """
        全局刮削弹幕
        """
        if not self._path:
            logger.warning("未设置刮削路径，跳过刮削")
            return schemas.Response(success=False, message="没有设定路径")

        logger.info("开始弹幕刮削")
        
        threading_list = []
        paths = [path.strip() for path in self._path.split('\n') if path.strip()]

        # 计算总文件数
        total_files = 0
        for path in paths:
            if not os.path.exists(path):
                logger.warning(f"路径不存在: {path}")
                return schemas.Response(success=False, message=f"路径不存在: {path}")

            if os.path.isfile(path) and path.endswith(('.mp4', '.mkv')):
                total_files += 1
            else:
                for root, _, files in os.walk(path):
                    total_files += sum(1 for file in files if file.endswith(('.mp4', '.mkv')))

        for path in paths:
            if not os.path.exists(path):
                continue

            # 检查是否是单个文件
            if os.path.isfile(path) and path.endswith(('.mp4', '.mkv')):
                logger.info(f"刮削单个文件：{path}")
                if len(threading_list) >= self._max_threads:
                    threading_list[0].join()
                    threading_list.pop(0)

                thread = threading.Thread(
                    target=self.generate_danmu,
                    args=(path,)
                )
                thread.start()
                threading_list.append(thread)
                continue

            # 处理目录
            logger.info(f"刮削路径：{path}")
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(('.mp4', '.mkv')):
                        if len(threading_list) >= self._max_threads:
                            threading_list[0].join()
                            threading_list.pop(0)

                        target_file = os.path.join(root, file)
                        logger.info(f"开始生成弹幕文件：{target_file}")
                        thread = threading.Thread(
                            target=self.generate_danmu,
                            args=(target_file,)
                        )
                        thread.start()
                        threading_list.append(thread)

        for thread in threading_list:
            thread.join()

        logger.info("弹幕刮削完成")
        return schemas.Response(success=True, message="弹幕刮削完成")
    
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
            thread = threading.Thread(
                target=self.generate_danmu,
                args=(target_file,)
            )
            thread.start()
        except Exception as e:
            logger.error(f"处理传输完成事件失败: {e}")

    def stop_service(self):
        """
        退出插件
        """
        pass

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

    def scan_path(self, path: str = None) -> Dict[str, Any]:
        """
        扫描路径下的媒体文件和弹幕信息
        :param path: 要扫描的路径
        :return: 目录结构信息
        """
        if not path:
            path = self._path
            
        if not path or not os.path.exists(path):
            return schemas.Response(success=False, message="路径不存在")
            
        result = {
            "name": os.path.basename(path),
            "path": path,
            "type": "directory",
            "children": []
        }
        
        try:
            # 如果是文件
            if os.path.isfile(path):
                if path.endswith(('.mp4', '.mkv')):
                    result["type"] = "media"
                    # 检查是否存在对应的弹幕文件
                    logger.info(f"检查弹幕文件: {path}")
                    ass_file = f"{os.path.splitext(path)[0]}.danmu.ass"
                    if os.path.exists(ass_file):
                        result["danmu_count"] = self.count_danmu_lines(ass_file)
                        logger.info(f"找到弹幕文件,数量: {result['danmu_count']}")
                    else:
                        result["danmu_count"] = 0
                        logger.info("未找到弹幕文件")
                return result
                
            # 如果是目录
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path):
                    if item.endswith(('.mp4', '.mkv')):
                        child = {
                            "name": item,
                            "path": item_path,
                            "type": "media",
                            "children": []
                        }
                        # 检查是否存在对应的弹幕文件
                        ass_file = f"{os.path.splitext(item_path)[0]}.danmu.ass"
                        if os.path.exists(ass_file):
                            child["danmu_count"] = self.count_danmu_lines(ass_file)
                        else:
                            child["danmu_count"] = 0
                        result["children"].append(child)
                elif os.path.isdir(item_path):
                    child = {
                        "name": item,
                        "path": item_path,
                        "type": "directory",
                        "children": []
                    }
                    result["children"].append(child)
                    
            return schemas.Response(success=True, data=result)
        except Exception as e:
            logger.error(f"扫描路径失败: {e}")
            return schemas.Response(success=False, message=f"扫描路径失败: {str(e)}")

    def generate_danmu_single(self, file_path: str) -> Dict[str, Any]:
        """
        为单个文件生成弹幕
        :param file_path: 媒体文件路径
        :return: 生成结果
        """
        if not file_path or not os.path.exists(file_path):
            return schemas.Response(success=False, message="文件不存在")
            
        if not file_path.endswith(('.mp4', '.mkv')):
            return schemas.Response(success=False, message="不支持的文件格式")
            
        try:
            result = self.generate_danmu(file_path)
            if result is None:
                return schemas.Response(success=False, message="弹幕生成失败")
            # 如果是字符串且不是弹幕文件路径，说明是失败原因
            if isinstance(result, str) and not result.endswith('.ass'):
                return schemas.Response(success=False, message=result)
            # 正常生成
            ass_file = f"{os.path.splitext(file_path)[0]}.danmu.ass"
            danmu_count = self.count_danmu_lines(ass_file)
            logger.info(f"生成弹幕成功，弹幕数量: {danmu_count}")
            if danmu_count == 0:
                return schemas.Response(success=False, message="弹幕数量为0 跳过生成")
            return schemas.Response(
                success=True,
                message="弹幕生成成功",
                data={
                    "danmu_count": danmu_count,
                    "file_path": file_path
                }
            )
        except Exception as e:
            logger.error(f"生成弹幕失败: {e}")
            return schemas.Response(success=False, message=f"生成弹幕失败: {str(e)}")
