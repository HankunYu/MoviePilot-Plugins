import chardet
import requests
import os
import re
import hashlib
import subprocess
import json
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from app.log import logger

@dataclass
class VideoInfo:
    file_name: str
    file_hash: str
    file_size: int
    video_duration: int
    match_mode: str = "hashAndFileName"

class StrmProcessor:
    @staticmethod
    def is_strm_file(file_path: str) -> bool:
        """检查是否为.strm文件"""
        return file_path.lower().endswith('.strm')
    
    @staticmethod
    def get_strm_url(file_path: str) -> Optional[str]:
        """读取.strm文件获取流媒体URL"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                url = f.read().strip()
                logger.info(f"从.strm文件读取到URL: {url}")
                return url if url else None
        except Exception as e:
            logger.error(f"读取.strm文件失败: {e}")
            return None
    
    @staticmethod
    def create_fake_video_info(file_path: str) -> VideoInfo:
        """为.strm文件创建虚拟的VideoInfo对象，用于TMDB匹配"""
        file_name = os.path.basename(file_path)
        # 使用文件名作为hash（确保唯一性）
        fake_hash = hashlib.md5(file_name.encode()).hexdigest()
        
        return VideoInfo(
            file_name=file_name,
            file_hash=fake_hash,
            file_size=0,  # .strm文件大小通常很小，设为0
            video_duration=0,  # 无法获取时长，设为0
            match_mode="hashAndFileName"
        )

class DanmuAPI:
    BASE_URL = 'https://dandanapi.hankun.online/api/v1'
    HEADERS = {
        'Accept': 'application/json',
        "User-Agent": "Moviepilot/plugins 1.3.0"
    }
    MANUAL_MATCH_FILE = ".dandan.anime.json"

    @classmethod
    def _manual_file_path(cls, directory: str) -> str:
        return os.path.join(directory, cls.MANUAL_MATCH_FILE)

    @staticmethod
    def _normalize_episode(episode: Optional[int]) -> int:
        try:
            value = int(episode)
        except (TypeError, ValueError):
            value = 1
        return value if value > 0 else 1

    @classmethod
    def _compose_comment_id(cls, anime_id: Any, episode: Optional[int]) -> Optional[str]:
        try:
            anime_id_int = int(anime_id)
        except (TypeError, ValueError):
            return None
        episode_int = cls._normalize_episode(episode)
        return str(anime_id_int * 10000 + episode_int)

    @classmethod
    def _write_manual_mapping(cls, directory: str, data: Dict[str, Any]) -> None:
        if not directory:
            return
        anime_id = data.get("animeId") or data.get("anime_id")
        if anime_id is None:
            return
        try:
            anime_id_int = int(anime_id)
        except (TypeError, ValueError):
            logger.warning(f"手动匹配数据中的animeId无效: {anime_id}")
            return
        payload = dict(data)
        payload["animeId"] = anime_id_int
        payload.pop("anime_id", None)
        payload.setdefault("updatedAt", datetime.now().isoformat(timespec="seconds"))
        manual_path = cls._manual_file_path(directory)
        try:
            with open(manual_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            logger.info(f"已写入手动匹配文件: {manual_path}")
        except Exception as e:
            logger.error(f"写入手动匹配文件失败: {e}")

    @classmethod
    def _load_manual_mapping(cls, directory: str) -> Optional[Dict[str, Any]]:
        if not directory or not os.path.isdir(directory):
            return None

        manual_path = cls._manual_file_path(directory)
        if os.path.exists(manual_path):
            try:
                with open(manual_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                anime_id = data.get("animeId") or data.get("anime_id")
                if anime_id is not None:
                    return data
            except Exception as e:
                logger.warning(f"读取手动匹配文件失败: {e}")

        # 兼容旧的 .id 文件
        try:
            for file in os.listdir(directory):
                if not file.endswith('.id'):
                    continue
                legacy_path = os.path.join(directory, file)
                try:
                    anime_id = int(os.path.splitext(file)[0])
                except (TypeError, ValueError):
                    logger.warning(f"忽略无法解析的ID文件: {legacy_path}")
                    continue
                data = {
                    "animeId": anime_id,
                    "source": "legacy-id-file",
                    "updatedAt": datetime.now().isoformat(timespec="seconds")
                }
                cls._write_manual_mapping(directory, data)
                try:
                    os.remove(legacy_path)
                    logger.info(f"已转换旧的ID文件并移除: {legacy_path}")
                except Exception as err:
                    logger.warning(f"移除旧ID文件失败: {err}")
                return data
        except Exception as e:
            logger.warning(f"检查手动匹配目录失败: {e}")

        return None
    @staticmethod
    def calculate_md5_of_first_16MB(file_path: str) -> str:
        md5 = hashlib.md5()
        size_16MB = 16 * 1024 * 1024
        try:
            with open(file_path, 'rb') as f:
                data = f.read(size_16MB)
                md5.update(data)
            return md5.hexdigest()
        except Exception as e:
            logger.error(f"计算MD5失败: {e}")
            return ""

    @staticmethod
    def get_video_duration(file_path: str) -> Optional[float]:
        try:
            process = subprocess.Popen(
                ['ffmpeg', '-i', file_path],
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE
            )
            _, stderr = process.communicate()
            
            stderr = stderr.decode('utf-8', errors='ignore')
            duration_match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", stderr)
            
            if duration_match:
                hours, minutes, seconds = map(float, duration_match.groups())
                return hours * 3600 + minutes * 60 + seconds
            return None
        except Exception as e:
            logger.error(f"获取视频时长失败: {e}")
            return None

    @staticmethod
    def get_file_size(file_path: str) -> int:
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            logger.error(f"获取文件大小失败: {e}")
            return 0

    @staticmethod
    def search_by_tmdb_id(tmdb_id: int, episode: Optional[int] = None) -> Optional[str]:
        """
        使用TMDB ID搜索弹幕
        :param tmdb_id: TMDB ID
        :param episode: 集数
        :return: 弹幕ID
        """
        try:
            url = f"{DanmuAPI.BASE_URL}/search/tmdb"
            data = {
                "tmdb_id": tmdb_id
            }
            if episode is not None:
                data["episode"] = episode
            else:
                data["episode"] = 1
            response = requests.post(url, json=data, headers=DanmuAPI.HEADERS)
            if response.status_code == 200:
                result = response.json()
                if result.get("success") and not result.get("hasMore"):
                    animes = result.get("animes", [])
                    if animes and len(animes) > 0:
                        episodes = animes[0].get("episodes", [])
                        if episodes and len(episodes) > 0:
                            return str(episodes[0].get("episodeId"))
            return None
        except Exception as e:
            logger.error(f"使用TMDB ID搜索弹幕失败: {e}")
            return None

    @staticmethod
    def get_comment_id(file_path: str, use_tmdb_id: bool = False, tmdb_id: Optional[int] = None, episode: Optional[int] = None, cache_ttl: Optional[int] = None) -> Optional[str]:
        """
        获取弹幕ID
        :param file_path: 视频文件路径
        :param use_tmdb_id: 是否使用TMDB ID
        :param tmdb_id: TMDB ID
        :param episode: 集数
        :return: 弹幕ID
        """
        try:
            # 检查是否为.strm文件
            if StrmProcessor.is_strm_file(file_path):
                logger.info(f"检测到.strm文件: {file_path}")
                # 读取.strm文件内容
                strm_url = StrmProcessor.get_strm_url(file_path)
                if strm_url:
                    logger.info(f"STRM文件指向: {strm_url}")
                
                # 对于.strm文件，强制使用TMDB ID匹配
                if tmdb_id is not None:
                    logger.info(f"为.strm文件使用TMDB ID匹配: {tmdb_id}")
                    comment_id = DanmuAPI.search_by_tmdb_id(tmdb_id, episode)
                    if comment_id:
                        return comment_id
                else:
                    logger.warning(f".strm文件未提供TMDB ID，无法进行弹幕匹配: {file_path}")
                
                # .strm文件如果没有TMDB ID，直接返回None
                return None
            
            # 普通视频文件的处理逻辑
            file_name = os.path.basename(file_path)
            file_size = DanmuAPI.get_file_size(file_path)
            file_hash = DanmuAPI.calculate_md5_of_first_16MB(file_path)
            
            video_info = VideoInfo(
                file_name=file_name,
                file_hash=file_hash,
                file_size=file_size,
                video_duration=int(DanmuAPI.get_video_duration(file_path) or 0)
            )
            
            video_dir = os.path.dirname(file_path)
            manual_mapping = DanmuAPI._load_manual_mapping(video_dir)
            if manual_mapping:
                manual_comment = DanmuAPI._compose_comment_id(
                    manual_mapping.get("animeId") or manual_mapping.get("anime_id"),
                    episode
                )
                if manual_comment:
                    logger.info(f"使用目录手动匹配ID: {manual_comment}")
                    return manual_comment
            
            # 使用 match API
            url = f"{DanmuAPI.BASE_URL}/match"
            response = requests.post(url, json=video_info.__dict__, headers=DanmuAPI.HEADERS)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("isMatched") and result.get("matches"):
                    return str(result["matches"][0]["episodeId"])
            
            # 如果使用TMDB ID且提供了TMDB ID，尝试使用TMDB ID匹配
            if use_tmdb_id and tmdb_id is not None:
                comment_id = DanmuAPI.search_by_tmdb_id(tmdb_id, episode)
                if comment_id:
                    return comment_id
            
            return None
        except Exception as e:
            logger.error(f"获取弹幕ID失败: {e}")
            return None

    @staticmethod
    def get_title_from_nfo(file_path: str) -> Optional[str]:
        nfo_file = os.path.splitext(file_path)[0] + '.nfo'
        try:
            with open(nfo_file, 'r', encoding='utf-8') as f:
                nfo_content = f.read()
                title_match = re.search(r'<title>(.*)</title>', nfo_content)
                if title_match:
                    logger.info(f'从nfo文件中获取标题 - {title_match.group(1)}')
                    return title_match.group(1)
                logger.error('未找到标题信息')
                return None
        except Exception as e:
            logger.error(f'读取nfo文件失败: {e}')
            return None

    @classmethod
    def get_comments(cls, comment_id: str) -> Optional[Dict]:
        """
        获取弹幕内容
        :param comment_id: 弹幕ID
        :return: 弹幕数据
        """
        try:
            url = f"{cls.BASE_URL}/{comment_id}?from_id=0&with_related=true&ch_convert=0"
            response = requests.get(url, headers=cls.HEADERS)
            if response.status_code == 200:
                return response.json()
            logger.error(f"获取弹幕失败: {response.text}")
            return None
        except Exception as e:
            logger.error(f"获取弹幕失败: {e}")
            return None

class DanmuConverter:
    @staticmethod
    def convert_timestamp(timestamp: float) -> str:
        timestamp = round(timestamp * 100.0)
        hour, minute = divmod(timestamp, 360000)
        minute, second = divmod(minute, 6000)
        second, centsecond = divmod(second, 100)
        return f'{int(hour)}:{int(minute):02d}:{int(second):02d}.{int(centsecond):02d}'

    @staticmethod
    def write_ass_head(f, width: int, height: int, fontface: str, fontsize: float, alpha: float, styleid: str):
        # 将透明度从0-1转换为0-255，并反转（因为ASS中0是完全不透明，255是完全透明）
        alpha_value = int((1 - alpha) * 255)
        f.write(
            f'''[Script Info]
; Script generated by Hankun 
; Super thanks to https://github.com/m13253/danmaku2ass and https://www.dandanplay.com/
Script Updated By: MoviePilot Danmu Plugin https://github.com/HankunYu/MoviePilot-Plugins
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
Aspect Ratio: {width}:{height}
Collisions: Normal
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: {styleid}, {fontface}, {fontsize:.0f}, &H{alpha_value:02X}FFFFFF, &H{alpha_value:02X}FFFFFF, &H{alpha_value:02X}000000, &H{alpha_value:02X}000000, 0, 0, 0, 0, 100, 100, 0.00, 0.00, 1, {max(fontsize / 25.0, 1):.0f}, 0, 7, 0, 0, 0, 0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
        )

    @staticmethod
    def find_non_overlapping_track(tracks: Dict[int, float], current_time: float, max_tracks: int) -> Optional[int]:
        for track in range(1, max_tracks + 1):
            if track not in tracks or current_time >= tracks[track]:
                return track
        # 所有轨道都被占用时返回None，避免强行使用忙碌轨道导致重叠
        return None

    @classmethod
    def convert_comments_to_ass(cls, comments: List[Dict], output_file: str, width: int, 
                              height: int, fontface: str, fontsize: float, alpha: float, duration: float, screen_area: str = 'full'):
        styleid = 'Danmu'
        
        # 根据屏幕区域计算有效高度和轨道数
        if screen_area == 'half':
            effective_height = height // 2  # 上半屏
            logger.info(f"使用半屏弹幕模式，有效高度: {effective_height}")
        elif screen_area == 'quarter':
            effective_height = height // 4  # 上1/4屏
            logger.info(f"使用1/4屏弹幕模式，有效高度: {effective_height}")
        else:  # full
            effective_height = height
            logger.info(f"使用全屏弹幕模式，有效高度: {effective_height}")
        
        max_tracks = int(effective_height) // int(fontsize)
        logger.info(f"最大弹幕轨道数: {max_tracks}")
        
        scrolling_tracks = {}
        top_tracks = {}
        bottom_tracks = {}

        logger.info(f"{output_file} - 共匹配到{len(comments)}条弹幕。")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            cls.write_ass_head(f, width, height, fontface, fontsize, alpha, styleid)
            
            for comment in comments:
                try:
                    p = comment.get('p', '').split(',')
                    if len(p) < 3:
                        logger.warning(f"弹幕数据格式不正确: {comment}")
                        continue
                    
                    timeline = float(p[0])
                    pos = int(p[1])
                    color = int(p[2])
                    text = comment.get('m', '')
                    user = str(p[3])
                    
                    if not text:
                        continue
                        
                    start_time = cls.convert_timestamp(timeline)
                    end_time = cls.convert_timestamp(timeline + duration)
                    
                    gap = 1
                    text_width = len(text) * fontsize * 0.6
                    velocity = (width + text_width) / duration
                    leave_time = text_width / velocity + gap

                    color_hex = f'&H{color & 0xFFFFFF:06X}'
                    styles = ''
                    
                    if pos == 1:  # 滚动弹幕
                        track_id = cls.find_non_overlapping_track(scrolling_tracks, timeline, max_tracks)
                        if track_id is None:
                            continue  # 全部轨道占用，跳过避免重叠
                        scrolling_tracks[track_id] = timeline + leave_time
                        initial_y = (track_id - 1) * fontsize + 10
                        styles = f'\\move({width}, {initial_y}, {-len(text)*fontsize}, {initial_y})'
                    elif pos == 4:  # 底部弹幕
                        track_id = cls.find_non_overlapping_track(bottom_tracks, timeline, max_tracks)
                        if track_id is None:
                            continue  # 全部轨道占用，跳过避免重叠
                        bottom_tracks[track_id] = timeline + duration
                        # 底部弹幕需要根据屏幕区域调整位置
                        if screen_area == 'half':
                            bottom_y = effective_height - 10 - (track_id - 1) * fontsize
                        elif screen_area == 'quarter':
                            bottom_y = effective_height - 10 - (track_id - 1) * fontsize
                        else:
                            bottom_y = height - 50 - (track_id - 1) * fontsize
                        styles = f'\\an2\\pos({width/2}, {bottom_y})'
                    elif pos == 5:  # 顶部弹幕
                        track_id = cls.find_non_overlapping_track(top_tracks, timeline, max_tracks)
                        if track_id is None:
                            continue  # 全部轨道占用，跳过避免重叠
                        top_tracks[track_id] = timeline + duration
                        styles = f'\\an8\\pos({width/2}, {50 + (track_id - 1) * fontsize})'
                    else:
                        styles = f'\\move(0, 0, {width}, 0)'

                    f.write(f'Dialogue: 0,{start_time},{end_time},{styleid},,0,0,0,,{{\\c{color_hex}{styles}}}{text}\n')
                except Exception as e:
                    logger.error(f"处理弹幕数据失败: {e}, 弹幕数据: {comment}")
                    continue
            
            logger.info('弹幕生成成功 - ' + output_file)

class SubtitleProcessor:
    @staticmethod
    def get_video_streams(file_path: str) -> Dict:
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-print_format', 'json', '-show_format', '-show_streams', file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            return json.loads(result.stdout) if result.returncode == 0 else {}
        except Exception as e:
            logger.error(f"获取视频流信息失败: {e}")
            return {}

    @staticmethod
    def get_video_resolution(file_path: str) -> Tuple[int, int]:
        """
        获取视频的真实分辨率
        :param file_path: 视频文件路径
        :return: (宽度, 高度) 元组
        """
        try:
            # .strm文件无法直接获取视频分辨率，使用默认值
            if StrmProcessor.is_strm_file(file_path):
                logger.info(f".strm文件使用默认分辨率: 1920x1080")
                return 1920, 1080
            
            streams_info = SubtitleProcessor.get_video_streams(file_path)
            for stream in streams_info.get('streams', []):
                if stream.get('codec_type') == 'video':
                    width = stream.get('width', 1920)
                    height = stream.get('height', 1080)
                    logger.info(f"检测到视频分辨率: {width}x{height}")
                    return width, height
            logger.warning(f"未找到视频流，使用默认分辨率: 1920x1080")
            return 1920, 1080
        except Exception as e:
            logger.error(f"获取视频分辨率失败: {e}，使用默认分辨率: 1920x1080")
            return 1920, 1080

    @staticmethod
    def extract_subtitles(file_path: str, output_file: str, stream_index: int) -> bool:
        try:
            result = subprocess.run(
                ['ffmpeg', '-i', file_path, '-map', f'0:{stream_index}', '-c:s', 'ass', output_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"提取字幕失败: {e}")
            return False

    @classmethod
    def try_extract_sub(cls, file_path: str):
        streams_info = cls.get_video_streams(file_path)
        for stream in streams_info.get('streams', []):
            if stream.get('codec_type') == 'subtitle':
                stream_index = stream['index']
                base_name = os.path.splitext(file_path)[0]
                language = stream.get('tags', {}).get('language', 'unknown')
                
                if language not in ['zh', 'zho', 'chi', 'chs', 'cht', 'cn']:
                    continue
                    
                output_file = f"{base_name}.{language}.ass"
                if os.path.exists(output_file):
                    os.remove(output_file)
                    
                if cls.extract_subtitles(file_path, output_file, stream_index):
                    logger.info(f'成功提取内嵌字幕 - {output_file}')
                    break

    @staticmethod
    def find_subtitle_file(file_path: str) -> Optional[str]:
        filename = os.path.splitext(os.path.basename(file_path))[0]
        for root, _, files in os.walk(os.path.dirname(file_path)):
            for file in files:
                if (file.endswith(('.srt', '.ass', '.ssa')) and 
                    'danmu' not in file and 
                    file.startswith(filename)):
                    sub2 = os.path.join(root, file)
                    logger.info(f"找到字幕文件 - {sub2}")
                    return sub2
        logger.info("没找到字幕文件")
        return None
    
    @staticmethod
    def can_extract_subtitles(file_path: str) -> bool:
        """检查是否可以从文件中提取字幕"""
        # .strm文件无法提取内嵌字幕
        return not StrmProcessor.is_strm_file(file_path)

    @staticmethod
    def combine_sub_ass(sub1: str, sub2: str, video_file_path: str = None) -> bool:
        if not sub1 or not sub2:
            return False
        
        try:
            with open(sub1, 'r', encoding='utf-8-sig') as f:
                sub1_content = f.read()
            
            with open(sub2, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                file_encoding = result['encoding']
            
            with open(sub2, 'r', encoding=file_encoding) as f:
                sub2_content = f.read()
                
            if os.path.splitext(sub2)[1].lower() in ['.ass', '.ssa']:
                # 获取弹幕文件的分辨率（这是正确的分辨率）
                sub1ResX = re.search(r"PlayResX:\s*(\d+)", sub1_content)
                sub1ResY = re.search(r"PlayResY:\s*(\d+)", sub1_content)
                
                # 获取原字幕文件的分辨率（可能不准确）
                sub2ResX = re.search(r"PlayResX:\s*(\d+)", sub2_content)
                sub2ResY = re.search(r"PlayResY:\s*(\d+)", sub2_content)
                
                # 如果有视频文件路径，获取真实的视频分辨率
                if video_file_path:
                    video_width, video_height = SubtitleProcessor.get_video_resolution(video_file_path)
                    logger.info(f"使用视频真实分辨率: {video_width}x{video_height}")
                    
                    # 修正字幕文件的分辨率信息
                    if sub2ResX and sub2ResY:
                        old_width = int(sub2ResX.group(1))
                        old_height = int(sub2ResY.group(1))
                        logger.info(f"原字幕分辨率: {old_width}x{old_height}")
                        
                        # 如果原字幕分辨率明显不对（比如小于视频分辨率的一半），使用视频分辨率
                        if old_width < video_width // 2 or old_height < video_height // 2:
                            logger.warning(f"检测到字幕分辨率异常，从 {old_width}x{old_height} 修正为 {video_width}x{video_height}")
                            sub2_content = sub2_content.replace(f"PlayResX: {old_width}", f"PlayResX: {video_width}")
                            sub2_content = sub2_content.replace(f"PlayResY: {old_height}", f"PlayResY: {video_height}")

                fontSizeRatio = 1
                if sub1ResX and sub2ResX:
                    fontSizeRatio = int(sub1ResX.group(1)) / int(sub2ResX.group(1)) * 0.8

                format_match = re.search(r"Format:.+", sub2_content)
                if not format_match:
                    return False

                style_lines = re.findall(r'Style:.*', sub2_content)
                for i, line in enumerate(style_lines):
                    elements = line.split(',')
                    if len(elements) >= 3:
                        elements[2] = str(int(float(elements[2]) * fontSizeRatio))
                    # 保持原描边/阴影不变，仅调整字号
                    style_lines[i] = ','.join(elements)

                events_start = sub2_content.find('[Events]')
                if events_start == -1:
                    return False

                events_content = sub2_content[events_start + len('[Events]'):].strip()
                output = os.path.splitext(sub2)[0] + ".withDanmu.ass"
                
                # 为原字幕事件追加柔和模糊标签，增强可读性
                # 只对普通底部字幕添加blur，特效字幕（有定位标签或特殊样式名）不添加
                def _apply_blur(events_text: str, blur_value: int = 10) -> str:
                    # Position tags that indicate special subtitle (not regular bottom dialogue)
                    # Note: \fad and \t are excluded as they're commonly used in normal dialogue
                    effect_tags = (r'\pos', r'\move', r'\org', r'\clip', r'\iclip')
                    # Style names that typically indicate effect/sign subtitles
                    effect_style_keywords = ('sign', 'title', 'op', 'ed', 'screen', 'note',
                                             'comment', 'insert', 'overlap', 'flashback',
                                             'song', 'karaoke')

                    def _is_effect_subtitle(style_name: str, text: str) -> bool:
                        """Check if this is an effect subtitle that should not have blur"""
                        # Check style name for effect keywords
                        style_lower = style_name.lower()
                        for keyword in effect_style_keywords:
                            if keyword in style_lower:
                                return True
                        # Check for position/effect tags in text
                        for tag in effect_tags:
                            if tag in text:
                                return True
                        # Check for \an tag with non-bottom alignment (1,2,3 are bottom)
                        an_match = re.search(r'\\an(\d)', text)
                        if an_match and int(an_match.group(1)) > 3:
                            return True
                        # Check for legacy \a tag with non-bottom alignment
                        # \a1,\a2,\a3 are bottom; \a5,\a6,\a7 are top; \a9,\a10,\a11 are middle
                        a_match = re.search(r'\\a(\d+)', text)
                        if a_match:
                            a_val = int(a_match.group(1))
                            if a_val not in (1, 2, 3):
                                return True
                        return False

                    lines = []
                    for line in events_text.splitlines():
                        if not line.startswith('Dialogue:'):
                            lines.append(line)
                            continue
                        parts = line.split(',', 9)
                        if len(parts) < 10:
                            lines.append(line)
                            continue

                        style_name = parts[3] if len(parts) > 3 else ''
                        text = parts[9]

                        # Skip blur for effect subtitles
                        if _is_effect_subtitle(style_name, text):
                            lines.append(line)
                            continue

                        if text.startswith('{'):
                            text = '{\\blur' + str(blur_value) + text[1:]
                        else:
                            text = '{\\blur' + str(blur_value) + '}' + text
                        parts[9] = text
                        lines.append(','.join(parts))
                    return '\n'.join(lines)

                events_content_with_blur = _apply_blur(events_content, blur_value=10)

                with open(output, 'w', encoding='utf-8-sig') as f:
                    f.write(sub1_content)
                    f.write('\n[V4+ Styles]\n')
                    f.write(format_match.group())
                    f.write('\n')
                    f.write('\n'.join(style_lines))
                    f.write('\n[Events]\n')
                    f.write(events_content_with_blur)
                
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"合并字幕失败: {e}")
            return False

def danmu_generator(file_path: str, width: int = 1920, height: int = 1080,
                   fontface: str = 'Arial', fontsize: float = 50,
                   alpha: float = 0.8, duration: float = 6, onlyFromBili: bool = False,
                   use_tmdb_id: bool = False, tmdb_id: Optional[int] = None,
                   episode: Optional[int] = None, cache_ttl: Optional[int] = None,
                   screen_area: str = 'full', manual_comment_id: Optional[str] = None) -> Optional[str]:
    try:
        comment_id = manual_comment_id or DanmuAPI.get_comment_id(
            file_path, use_tmdb_id, tmdb_id, episode, cache_ttl
        )
        if not comment_id:
            logger.info(f"未找到对应弹幕 - {file_path}")
            return "未找到对应弹幕"

        comments_data = DanmuAPI.get_comments(comment_id)
        if not comments_data:
            return "未获取到弹幕数据"

        comments = sorted(comments_data["comments"], key=lambda x: float(x['p'].split(',')[0]))
        
        if len(comments) == 0:
            logger.info(f"弹幕数量为0，跳过生成 - {file_path}")
            return f"弹幕数量为0，跳过生成 - {file_path}"

        # 过滤B站弹幕
        if onlyFromBili:
            comments = [comment for comment in comments if '[BiliBili]' in comment['p'].split(',')[3]]
            logger.info(f"过滤后剩余{len(comments)}条B站弹幕")

        output_file = os.path.splitext(file_path)[0] + '.danmu.ass'
        
        DanmuConverter.convert_comments_to_ass(
            comments, output_file, 
            width=int(width), 
            height=int(height), 
            fontface=fontface, 
            fontsize=float(fontsize), 
            alpha=float(alpha), 
            duration=float(duration),
            screen_area=screen_area
        )

        # 处理字幕合并
        sub2 = SubtitleProcessor.find_subtitle_file(file_path)
        
        # 只有非.strm文件才尝试提取内嵌字幕
        if not sub2 and SubtitleProcessor.can_extract_subtitles(file_path):
            SubtitleProcessor.try_extract_sub(file_path)
            sub2 = SubtitleProcessor.find_subtitle_file(file_path)

        if sub2:
            SubtitleProcessor.combine_sub_ass(output_file, sub2, file_path)
        else:
            if StrmProcessor.is_strm_file(file_path):
                logger.info(f'.strm文件未找到外部字幕，仅生成弹幕文件 - {file_path}')
            else:
                logger.error(f'未找到原生字幕，跳过合并 - {file_path}')

        return output_file

    except Exception as e:
        logger.error(f"生成弹幕失败: {e}")
        return f"生成弹幕失败: {str(e)}"
