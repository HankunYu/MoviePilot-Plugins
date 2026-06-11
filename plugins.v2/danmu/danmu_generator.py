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
        "User-Agent": "Moviepilot/plugins 1.8.0"
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
            try:
                _, stderr = process.communicate(timeout=120)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                logger.error(f"获取视频时长超时(120s): {file_path}")
                return None

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
    def search_by_tmdb_id(tmdb_id: int, episode: Optional[int] = None,
                          tmdb_id_type: int = 0) -> Optional[str]:
        """
        使用TMDB ID搜索弹幕
        :param tmdb_id: TMDB ID
        :param episode: 集数
        :param tmdb_id_type: TMDB ID类型，0=电视剧，1=电影
        :return: 弹幕ID
        """
        try:
            url = f"{DanmuAPI.BASE_URL}/search/tmdb"
            data = {
                "tmdb_id": tmdb_id,
                "tmdb_id_type": tmdb_id_type
            }
            # Server requires episode but ignores it for movies (type=1)
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
    def get_comment_id(file_path: str, use_tmdb_id: bool = False, tmdb_id: Optional[int] = None, episode: Optional[int] = None, cache_ttl: Optional[int] = None, tmdb_id_type: int = 0) -> Optional[str]:
        """
        获取弹幕ID
        :param file_path: 视频文件路径
        :param use_tmdb_id: 是否使用TMDB ID
        :param tmdb_id: TMDB ID
        :param episode: 集数
        :param tmdb_id_type: TMDB ID类型，0=电视剧，1=电影
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
                    comment_id = DanmuAPI.search_by_tmdb_id(tmdb_id, episode, tmdb_id_type)
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
                comment_id = DanmuAPI.search_by_tmdb_id(tmdb_id, episode, tmdb_id_type)
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
    def get_comments(cls, comment_id: str, cache_ttl: Optional[int] = None) -> Optional[Dict]:
        """
        获取弹幕内容
        :param comment_id: 弹幕ID
        :param cache_ttl: 缓存时间（分钟），传给中转服务器控制缓存
        :return: 弹幕数据
        """
        try:
            url = f"{cls.BASE_URL}/{comment_id}?from_id=0&with_related=true&ch_convert=0"
            if cache_ttl is not None:
                url += f"&cache_ttl={cache_ttl}"
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
        ass_candidates = []
        srt_candidates = []
        for root, _, files in os.walk(os.path.dirname(file_path)):
            for file in files:
                if 'danmu' in file or not file.startswith(filename):
                    continue
                full_path = os.path.join(root, file)
                if file.endswith(('.ass', '.ssa')):
                    ass_candidates.append(full_path)
                elif file.endswith('.srt'):
                    srt_candidates.append(full_path)
        # Prefer .ass/.ssa over .srt for richer style information
        if ass_candidates:
            logger.info(f"找到字幕文件 - {ass_candidates[0]}")
            return ass_candidates[0]
        if srt_candidates:
            logger.info(f"找到字幕文件 - {srt_candidates[0]}")
            return srt_candidates[0]
        logger.info("没找到字幕文件")
        return None
    
    @staticmethod
    def can_extract_subtitles(file_path: str) -> bool:
        """检查是否可以从文件中提取字幕"""
        # .strm文件无法提取内嵌字幕
        return not StrmProcessor.is_strm_file(file_path)

    @staticmethod
    def _convert_srt_timestamp_to_ass(srt_ts: str) -> str:
        """Convert SRT timestamp HH:MM:SS,mmm to ASS H:MM:SS.CC"""
        srt_ts = srt_ts.strip().replace(',', '.')
        parts = srt_ts.split(':')
        if len(parts) != 3:
            return '0:00:00.00'
        hours = int(parts[0])
        minutes = int(parts[1])
        sec_parts = parts[2].split('.')
        seconds = int(sec_parts[0])
        ms_str = sec_parts[1] if len(sec_parts) > 1 else '0'
        ms_str = ms_str.ljust(3, '0')[:3]  # Normalize to exactly 3 digits
        centiseconds = int(ms_str) // 10
        return f'{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}'

    @staticmethod
    def _parse_srt_to_ass_events(srt_content: str, style_name: str) -> List[str]:
        """Parse SRT content into ASS Dialogue lines"""
        # Strip HTML tags commonly found in SRT
        html_tag_re = re.compile(r'<[^>]+>')
        timestamp_re = re.compile(
            r'(\d+:\d{2}:\d{2}[,.]\d+)\s*-->\s*(\d+:\d{2}:\d{2}[,.]\d+)'
        )

        # Normalize line endings (handles \r\n and \r)
        srt_content = srt_content.replace('\r\n', '\n').replace('\r', '\n')
        blocks = re.split(r'\n\s*\n', srt_content.strip())
        lines = []
        for block in blocks:
            block_lines = block.strip().splitlines()
            if len(block_lines) < 2:
                continue

            ts_match = None
            text_start = 0
            for i, line in enumerate(block_lines):
                ts_match = timestamp_re.search(line)
                if ts_match:
                    text_start = i + 1
                    break

            if not ts_match or text_start >= len(block_lines):
                continue

            start = SubtitleProcessor._convert_srt_timestamp_to_ass(ts_match.group(1))
            end = SubtitleProcessor._convert_srt_timestamp_to_ass(ts_match.group(2))

            # Join multiline text with ASS line break \N and strip HTML tags
            text_parts = []
            for tl in block_lines[text_start:]:
                cleaned = html_tag_re.sub('', tl.strip())
                if cleaned:
                    text_parts.append(cleaned)
            text = r'\N'.join(text_parts)

            if text:
                lines.append(
                    f'Dialogue: 0,{start},{end},{style_name},,0,0,0,,{text}'
                )
        return lines

    @staticmethod
    def _generate_srt_ass_style(width: int, fontface: str, fontsize: float) -> str:
        """Generate an ASS style line for SRT subtitles (white text, black border, bottom center)"""
        return (
            f'Style: SubtitleSRT, {fontface}, {fontsize:.0f}, '
            f'&H00FFFFFF, &H00FFFFFF, &H00000000, &H80000000, '
            f'0, 0, 0, 0, 100, 100, 0.00, 0.00, 1, '
            f'{max(fontsize / 25.0, 1):.0f}, 0, 2, 20, 20, 20, 0'
        )

    @staticmethod
    def _scale_ass_events(events_text: str, ratio_x: float, ratio_y: float) -> str:
        """Scale absolute coordinates and inline font sizes in ASS Dialogue lines.

        Handles: \\pos, \\org, \\move (first 4 coords), rectangular \\clip/\\iclip,
        and inline \\fs overrides.  Does NOT touch vector clips or \\p drawing paths.
        """

        def _scale_coord_pair(m: re.Match) -> str:
            """Scale a 2-arg tag like \\pos(x,y) or \\org(x,y)"""
            tag = m.group(1)
            x = float(m.group(2)) * ratio_x
            y = float(m.group(3)) * ratio_y
            return f'\\{tag}({x:.2f},{y:.2f})'

        def _scale_move(m: re.Match) -> str:
            """Scale \\move(x1,y1,x2,y2[,t1,t2]) — only scale the first 4 coords"""
            x1 = float(m.group(1)) * ratio_x
            y1 = float(m.group(2)) * ratio_y
            x2 = float(m.group(3)) * ratio_x
            y2 = float(m.group(4)) * ratio_y
            rest = m.group(5)  # optional ",t1,t2" or empty
            return f'\\move({x1:.2f},{y1:.2f},{x2:.2f},{y2:.2f}{rest})'

        def _scale_rect_clip(m: re.Match) -> str:
            """Scale rectangular \\clip(x1,y1,x2,y2) or \\iclip(...)"""
            tag = m.group(1)  # "clip" or "iclip"
            x1 = float(m.group(2)) * ratio_x
            y1 = float(m.group(3)) * ratio_y
            x2 = float(m.group(4)) * ratio_x
            y2 = float(m.group(5)) * ratio_y
            return f'\\{tag}({x1:.2f},{y1:.2f},{x2:.2f},{y2:.2f})'

        def _scale_fs(m: re.Match) -> str:
            """Scale inline \\fs (but not \\fsp, \\fscx, \\fscy)"""
            size = float(m.group(1)) * ratio_y
            return f'\\fs{size:.0f}'

        # Pre-compile patterns
        # \pos(x,y) or \org(x,y) — closing ')' is optional for malformed ASS
        re_coord_pair = re.compile(
            r'\\(pos|org)\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\)?'
        )
        # \move(x1,y1,x2,y2[,t1,t2]) — closing ')' is optional
        re_move = re.compile(
            r'\\move\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,'
            r'\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*((?:,\s*-?[\d.]+\s*,\s*-?[\d.]+\s*)?)\)?'
        )
        # Rectangular \clip / \iclip with exactly 4 numeric args — closing ')' is optional
        re_rect_clip = re.compile(
            r'\\(i?clip)\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,'
            r'\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\)?'
        )
        # Inline \fs followed by digits (not \fsp, \fscx, \fscy)
        re_fs = re.compile(r'\\fs(\d+(?:\.\d+)?)(?![a-zA-Z])')

        result_lines = []
        for line in events_text.splitlines():
            if not line.startswith('Dialogue:'):
                result_lines.append(line)
                continue

            # Scale Dialogue margins (parts[5]=MarginL, [6]=MarginR, [7]=MarginV)
            parts = line.split(',', 9)
            if len(parts) >= 10:
                for idx, ratio in ((5, ratio_x), (6, ratio_x), (7, ratio_y)):
                    val = parts[idx].strip()
                    if val and int(val) != 0:
                        parts[idx] = str(int(int(val) * ratio))
                line = ','.join(parts)

            # Scale override tags in the Text field
            line = re_coord_pair.sub(_scale_coord_pair, line)
            line = re_move.sub(_scale_move, line)
            line = re_rect_clip.sub(_scale_rect_clip, line)
            line = re_fs.sub(_scale_fs, line)
            result_lines.append(line)
        return '\n'.join(result_lines)

    # Style-name keywords that mark effect/sign subtitles (never blurred)
    _EFFECT_STYLE_KEYWORDS = ('sign', 'title', 'op', 'ed', 'screen', 'note',
                              'comment', 'insert', 'overlap', 'flashback',
                              'song', 'karaoke', 'staff', 'logo')
    # Inline tags that mark positioned/transformed lines.
    # \fad/\fade are common in plain dialogue and intentionally NOT listed.
    _EFFECT_TEXT_TAGS = ('\\pos', '\\move', '\\org', '\\clip', '\\iclip',
                         '\\fr', '\\fax', '\\fay', '\\t(')
    _RE_DRAWING_TAG = re.compile(r'\\p\d')      # \p1 drawing mode (\pos not matched: needs a digit)
    _RE_KARAOKE_TAG = re.compile(r'\\[kK][fo]?\d')

    @classmethod
    def _is_effect_dialogue(cls, style_name: str, text: str) -> bool:
        """
        判断是否为特效字幕行（定位/旋转/变换/绘图/卡拉OK等），特效行不加blur
        :param style_name: 样式名
        :param text: 事件文本字段
        """
        style_lower = style_name.lower()
        for keyword in cls._EFFECT_STYLE_KEYWORDS:
            if keyword in style_lower:
                return True
        for tag in cls._EFFECT_TEXT_TAGS:
            if tag in text:
                return True
        if cls._RE_DRAWING_TAG.search(text) or cls._RE_KARAOKE_TAG.search(text):
            return True
        # \an non-bottom alignment (1,2,3 are bottom)
        an_match = re.search(r'\\an(\d)', text)
        if an_match and int(an_match.group(1)) > 3:
            return True
        # Legacy \a non-bottom alignment
        a_match = re.search(r'\\a(\d+)', text)
        if a_match and int(a_match.group(1)) not in (1, 2, 3):
            return True
        return False

    @staticmethod
    def _resolve_playres(content: str) -> Tuple[Optional[int], Optional[int]]:
        """从ASS内容中解析PlayResX/PlayResY，缺失的返回None"""
        mx = re.search(r"PlayResX:\s*(\d+)", content)
        my = re.search(r"PlayResY:\s*(\d+)", content)
        return (int(mx.group(1)) if mx else None,
                int(my.group(1)) if my else None)

    @staticmethod
    def combine_sub_ass(sub1: str, sub2: str, video_file_path: str = None) -> bool:
        if not sub1 or not sub2:
            return False

        try:
            # If sub2 is already a merged file, use the original subtitle instead
            sub2_base, sub2_ext = os.path.splitext(sub2)
            if sub2_base.endswith('.withDanmu'):
                original_sub2 = sub2_base[:-len('.withDanmu')] + sub2_ext
                if os.path.exists(original_sub2):
                    logger.info(f"检测到已合并字幕，使用原始字幕: {original_sub2}")
                    sub2 = original_sub2
                else:
                    logger.warning(f"已合并字幕的原始文件不存在: {original_sub2}")
                    return False

            with open(sub1, 'r', encoding='utf-8-sig') as f:
                sub1_content = f.read()

            with open(sub2, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                file_encoding = result['encoding']

            with open(sub2, 'r', encoding=file_encoding) as f:
                sub2_content = f.read()
                
            if os.path.splitext(sub2)[1].lower() in ['.ass', '.ssa']:
                # Reverse-merge: the original subtitle is the base and is kept
                # byte-identical (header, styles, events untouched except the
                # optional blur tag on plain bottom dialogue). The danmu events
                # are rescaled INTO the original subtitle's coordinate space —
                # danmu is machine-generated (one style + \move/\pos only), so
                # scaling it is fully reliable, unlike scaling hand-authored
                # effect subtitles.

                # Danmu resolution: we always write PlayRes into the danmu header
                d_x, d_y = SubtitleProcessor._resolve_playres(sub1_content)
                d_x, d_y = d_x or 1920, d_y or 1080

                # Original resolution per ASS spec: both missing -> 384x288,
                # one missing -> derived from the other at 4:3
                s_x, s_y = SubtitleProcessor._resolve_playres(sub2_content)
                if s_x is None and s_y is None:
                    s_x, s_y = 384, 288
                elif s_x is None:
                    s_x = round(s_y * 4 / 3)
                elif s_y is None:
                    s_y = round(s_x * 3 / 4)

                ratio_x = s_x / d_x
                ratio_y = s_y / d_y
                need_scale = not (ratio_x == 1.0 and ratio_y == 1.0)
                if need_scale:
                    logger.info(
                        f"弹幕坐标缩放: danmu {d_x}x{d_y} -> 原字幕 {s_x}x{s_y}, "
                        f"ratio={ratio_x:.4f}x{ratio_y:.4f}"
                    )

                # Extract the danmu style line and dialogue events
                danmu_style_match = re.search(r'^Style:.*$', sub1_content, re.MULTILINE)
                if not danmu_style_match:
                    logger.error(f"弹幕文件中未找到样式行: {sub1}")
                    return False
                danmu_style_line = danmu_style_match.group()
                danmu_event_lines = [
                    line for line in sub1_content.splitlines()
                    if line.startswith('Dialogue:')
                ]

                if need_scale:
                    # Danmu style: Fontsize (idx 2) and Outline (idx 16) follow Y axis
                    fields = danmu_style_line.split(',')
                    if len(fields) >= 17:
                        fields[2] = f'{max(float(fields[2]) * ratio_y, 1):.0f}'
                        fields[16] = f'{max(float(fields[16]) * ratio_y, 0.5):.2f}'
                        danmu_style_line = ','.join(fields)
                    danmu_event_lines = SubtitleProcessor._scale_ass_events(
                        '\n'.join(danmu_event_lines), ratio_x, ratio_y
                    ).splitlines()

                # Rename the danmu style if it collides with an original style name
                danmu_style_name = danmu_style_line.split(':', 1)[1].split(',')[0].strip()
                sub2_style_names = {
                    line.split(':', 1)[1].split(',')[0].strip()
                    for line in re.findall(r'^Style:.*$', sub2_content, re.MULTILINE)
                }
                if danmu_style_name in sub2_style_names:
                    new_name = danmu_style_name
                    while new_name in sub2_style_names:
                        new_name += '_MP'
                    fields = danmu_style_line.split(',')
                    fields[0] = f'Style: {new_name}'
                    danmu_style_line = ','.join(fields)
                    renamed = []
                    for line in danmu_event_lines:
                        parts = line.split(',', 9)
                        if len(parts) >= 10:
                            parts[3] = new_name
                            renamed.append(','.join(parts))
                        else:
                            renamed.append(line)
                    danmu_event_lines = renamed
                    logger.info(f"弹幕样式名与原字幕冲突，重命名为: {new_name}")

                # Locate the original subtitle's sections to find insertion
                # points and collect per-style alignment for the blur filter
                sub2_lines = sub2_content.splitlines()
                section = None
                styles_format_idx = None    # v4+ styles Format line (danmu style goes after it)
                events_format_idx = None    # events Format line (danmu events go after it)
                events_fields = None        # parsed events Format fields, lowercased
                styles_fields = None
                style_alignments = {}       # style name -> Alignment value

                for i, raw in enumerate(sub2_lines):
                    line = raw.strip()
                    if line.startswith('[') and line.endswith(']'):
                        section = line.lower()
                        continue
                    lower = line.lower()
                    if section in ('[v4+ styles]', '[v4 styles]', '[v4++ styles]'):
                        if lower.startswith('format:'):
                            styles_fields = [f.strip().lower() for f in line.split(':', 1)[1].split(',')]
                            # Only insert our v4+ style line into a v4+ section
                            if section != '[v4 styles]' and styles_format_idx is None:
                                styles_format_idx = i
                        elif lower.startswith('style:') and styles_fields:
                            values = line.split(':', 1)[1].split(',')
                            try:
                                name_i = styles_fields.index('name')
                                align_i = styles_fields.index('alignment')
                                style_alignments[values[name_i].strip()] = int(float(values[align_i]))
                            except (ValueError, IndexError):
                                pass
                    elif section == '[events]':
                        if lower.startswith('format:') and events_format_idx is None:
                            events_fields = [f.strip().lower() for f in line.split(':', 1)[1].split(',')]
                            events_format_idx = i

                # Danmu events use the standard v4+ field order; if the original
                # declares a different one, fall back to a separate [Events] section
                standard_events = ['layer', 'start', 'end', 'style', 'name',
                                   'marginl', 'marginr', 'marginv', 'effect', 'text']
                events_insertable = events_fields == standard_events

                def _blur_dialogue(raw_line: str) -> str:
                    """为无特效的底部对白追加柔和模糊，提升纯白字幕在亮背景下的可读性"""
                    if not events_fields or events_fields[-1] != 'text':
                        return raw_line
                    text_i = len(events_fields) - 1
                    body = raw_line.split(':', 1)[1]
                    parts = body.split(',', text_i)
                    if len(parts) <= text_i:
                        return raw_line
                    style_name = parts[events_fields.index('style')].strip() \
                        if 'style' in events_fields else ''
                    effect_val = parts[events_fields.index('effect')].strip() \
                        if 'effect' in events_fields else ''
                    text = parts[text_i]
                    # Skip: Banner/Scroll effects, non-bottom styles, effect lines
                    if effect_val:
                        return raw_line
                    if style_alignments.get(style_name) not in (None, 1, 2, 3):
                        return raw_line
                    if SubtitleProcessor._is_effect_dialogue(style_name, text):
                        return raw_line
                    if text.startswith('{'):
                        parts[text_i] = '{\\blur10' + text[1:]
                    else:
                        parts[text_i] = '{\\blur10}' + text
                    return 'Dialogue:' + ','.join(parts)

                # Assemble: original lines pass through untouched (blur aside),
                # danmu style/events are inserted right after the Format lines
                output_lines = []
                in_events = False
                style_inserted = False
                events_inserted = False
                for i, raw in enumerate(sub2_lines):
                    stripped = raw.strip()
                    if stripped.startswith('[') and stripped.endswith(']'):
                        in_events = stripped.lower() == '[events]'
                    if in_events and raw.startswith('Dialogue:'):
                        output_lines.append(_blur_dialogue(raw))
                    else:
                        output_lines.append(raw)
                    if i == styles_format_idx:
                        output_lines.append(danmu_style_line)
                        style_inserted = True
                    if i == events_format_idx and events_insertable:
                        output_lines.extend(danmu_event_lines)
                        events_inserted = True

                # Fallbacks for non-standard structures: append separate
                # sections at the end (renderers merge same-named sections)
                if not style_inserted:
                    output_lines += [
                        '', '[V4+ Styles]',
                        'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, '
                        'OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, '
                        'ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, '
                        'Alignment, MarginL, MarginR, MarginV, Encoding',
                        danmu_style_line
                    ]
                if not events_inserted:
                    output_lines += [
                        '', '[Events]',
                        'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text'
                    ]
                    output_lines += danmu_event_lines

                output = os.path.splitext(sub2)[0] + ".withDanmu.ass"
                with open(output, 'w', encoding='utf-8-sig') as f:
                    f.write('\n'.join(output_lines))
                    f.write('\n')

                logger.info(f"字幕合并完成（原字幕保持原样）: {output}")
                return True

            elif os.path.splitext(sub2)[1].lower() == '.srt':
                # Parse SRT and convert to ASS events
                dialogue_lines = SubtitleProcessor._parse_srt_to_ass_events(
                    sub2_content, 'SubtitleSRT'
                )
                if not dialogue_lines:
                    logger.warning(f"SRT字幕解析为空: {sub2}")
                    return False

                # Get resolution from danmu file for style generation
                sub1ResX = re.search(r"PlayResX:\s*(\d+)", sub1_content)
                width = int(sub1ResX.group(1)) if sub1ResX else 1920
                srt_style = SubtitleProcessor._generate_srt_ass_style(
                    width, 'Arial', 50
                )

                # Apply blur to SRT dialogue lines
                blurred_lines = []
                for line in dialogue_lines:
                    parts = line.split(',', 9)
                    if len(parts) >= 10:
                        text = parts[9]
                        parts[9] = '{\\blur10}' + text
                        blurred_lines.append(','.join(parts))
                    else:
                        blurred_lines.append(line)

                output = os.path.splitext(sub2)[0] + ".withDanmu.ass"
                with open(output, 'w', encoding='utf-8-sig') as f:
                    f.write(sub1_content)
                    f.write('\n[V4+ Styles]\n')
                    f.write('Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n')
                    f.write(srt_style)
                    f.write('\n[Events]\n')
                    f.write('Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n')
                    f.write('\n'.join(blurred_lines))

                logger.info(f"SRT字幕合并完成: {output}")
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
                   screen_area: str = 'full', manual_comment_id: Optional[str] = None,
                   tmdb_id_type: int = 0) -> Optional[str]:
    try:
        comment_id = manual_comment_id or DanmuAPI.get_comment_id(
            file_path, use_tmdb_id, tmdb_id, episode, cache_ttl, tmdb_id_type
        )
        if not comment_id:
            logger.info(f"未找到对应弹幕 - {file_path}")
            return "未找到对应弹幕"

        comments_data = DanmuAPI.get_comments(comment_id, cache_ttl=cache_ttl)
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
