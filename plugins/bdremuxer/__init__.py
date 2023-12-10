import subprocess
import os
import ffmpeg
from pyparsebluray import mpls

# MoviePilot library
from app.log import logger
from app.plugins import _PluginBase
from app.core.event import eventmanager
from app.schemas.types import EventType
from app.utils.system import SystemUtils
from typing import Any, List, Dict, Tuple

class BDRemuxer(_PluginBase):
    # 插件名称
    plugin_name = "BDMV Remuxer"
    # 插件描述
    plugin_desc = "自动提取BDMV文件夹中的视频流和音频流，合并为MKV文件"
    # 插件图标
    plugin_icon = ""
    # 主题色
    plugin_color = "#3B5E8E"
    # 插件版本
    plugin_version = "0.1"
    # 插件作者
    plugin_author = "hankun"
    # 作者主页
    author_url = "https://github.com/hankunyu"
    # 插件配置项ID前缀
    plugin_config_prefix = "bdremuxer_"
    # 加载顺序
    plugin_order = 1
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _enabled = False


    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled")
        if self._enabled:
            logger.info("BD Remuxer 插件初始化完成")

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
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'info',
                                            'variant': 'flat',
                                            'text': '自用插件，不稳定，不保证可用性',
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
        }

    def get_page(self) -> List[dict]:
        pass
    
    def extract(self,bd_path : str) -> Tuple[bool, str]:
        output_name = os.path.basename(bd_path) + ".mkv"
        output_name = os.path.join(bd_path, output_name)
        bd_path = bd_path + '/BDMV'
        if not os.path.exists(bd_path):
            return False, '失败。输入路径不存在BDMV文件夹'
        mpls_path = bd_path + '/PLAYLIST/'
        if not os.path.exists(mpls_path):
            return False, '失败。找不到mpls文件'
        file_paths = self.get_all_m2ts(mpls_path)
        if not file_paths:
            return False, '失败。mpls中找不到播放列表'
        
        filelist_string = '\n'.join([f"file '{file}'" for file in file_paths])
        # 将filelist_string写入filelist.txt
        with open('/tmp/filelist.txt', 'w') as file:
            file.write(filelist_string)
            
        # 提取流程
        # 分析m2ts文件，提取视频流和音频流信息
        test_file = file_paths[0]
        probe = ffmpeg.probe(test_file)
        video_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'video']
        audio_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'audio']
        subtitle_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'subtitle']
        
        # 选取第一个视频流作为流编码信息
        video_codec = video_streams[0]['codec_name']
        # 获得每一条音频流的编码信息
        audio_codec = []
        for audio_stream in audio_streams:
            if audio_stream['codec_name'] == 'pcm_bluray':
                audio_codec.append('pcm_s16le')
            else:   
                audio_codec.append('copy')
            # print(audio_stream['codec_name'])
        
        # 获得每一条字幕流的编码信息
        subtitle_codec = []
        for subtitle_stream in subtitle_streams:
            if subtitle_stream['codec_name'] == 'hdmv_pgs_subtitle':
                subtitle_codec.append('copy')
            else:
                subtitle_codec.append('copy')
        
        # return True, 'test'
        # 整理参数作为字典
        dict = {  }
        for i in range(len(audio_codec)):
            dict[f'acodec:{i}'] = audio_codec[i]
        for i in range(len(subtitle_codec)):
            dict[f'scodec:{i}'] = subtitle_codec[i]
        # 使用ffmpeg合并m2ts文件
        try:
            (
            ffmpeg
            .input(
                '/tmp/filelist.txt', 
                format='concat', 
                safe=0, 
                )
            .output(
                output_name,
                vcodec='copy',
                **dict,
                map='0',  # 映射所有输入流
                map_metadata='0',  # 复制输入流的元数据
                map_chapters='0',  # 复制输入流的章节信息
            )
            .run()
            )
        except ffmpeg.Error as e:
            logger.error(e.stderr)
            return False, '失败。'
        return True, '成功。'
    

    def get_all_m2ts(self,mpls_path) -> list:
        """
        Get all useful m2ts file paths from mpls file
        :param mpls_path: path to mpls 00000 file
        :return: list of m2ts file paths
        """
        files = []
        play_items = []
        for file in os.listdir(mpls_path):
            if os.path.isfile(os.path.join(mpls_path, file)) and file.endswith('.mpls'):
                files.append(os.path.join(mpls_path, file))
        for file in files:
            with open(file, 'rb') as mpls_file:
                header = mpls.load_movie_playlist(mpls_file)
                mpls_file.seek(header.playlist_start_address, os.SEEK_SET)
                pls = mpls.load_playlist(mpls_file)
                for item in pls.play_items:
                    if item.uo_mask_table == 0:
                        stream_path = os.path.dirname(os.path.dirname(file)) + '/STREAM/'
                        file_path = stream_path + item.clip_information_filename + '.m2ts'
                        play_items.append(file_path)
                if play_items:
                    return play_items
        return play_items

    @eventmanager.register(EventType.NoticeMessage)
    def remux(self, event):

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

        # 检查是否存在BDMV文件夹
        bd_path = os.path.dirname(targets_file[0])
        if not os.path.exists(bd_path + '/BDMV'):
            return
        # 提取流程
        self.extract(bd_path)
        



    def stop_service(self):
        """
        退出插件
        """
        pass
