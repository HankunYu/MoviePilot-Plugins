import chardet
import requests
import os
import re
import hashlib
import subprocess
import json
import shutil
import threading
import time
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field
from app.log import logger


class DanmuThrottled(Exception):
    """
    服务端拒绝了本次请求（429 限速/日预算，或 503 配额熔断）。

    这表示传输层被拒绝，**不代表内容不存在**，因此调用方不得据此判定
    「未找到弹幕」，也不得计入重试次数。
    """

    def __init__(self, retry_after: float, status_code: Optional[int] = None):
        self.retry_after = retry_after
        self.status_code = status_code
        prefix = f"HTTP {status_code}" if status_code else "本地限速"
        super().__init__(f"弹弹API暂时不可用（{prefix}），约 {retry_after:.0f} 秒后可重试")


_warned_reasons = set()
_warn_lock = threading.Lock()


def _warn_once(key: str, message: str):
    """
    同一类环境问题只告警一次。批量刮削动辄上千文件，
    逐文件重复同一句话只会把信号淹掉。
    """
    with _warn_lock:
        if key in _warned_reasons:
            return
        _warned_reasons.add(key)
    logger.warning(message)


@dataclass
class SeriesLookup:
    """整季查询的结局。status: ok / absent / truncated / unknown"""
    status: str
    entries: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def usable(self) -> bool:
        """只有 ok 才能用来定位——truncated 的列表是残缺的，套公式会静默错位"""
        return self.status == "ok"


@dataclass
class DanmuResult:
    """
    一次刮削的结果分类。取代原来「返回值既可能是文件路径、又可能是失败原因」
    的字符串协议——调用方不必再靠 startswith/endswith 猜发生了什么。

    outcome:
      ok      —— 已生成弹幕文件
      absent  —— 弹弹play 未收录该内容（拿不到 episodeId）。**不是失败**
      empty   —— 已收录但服务端弹幕数为 0，弹幕可能之后才有
      failed  —— 真的出错了（网络、数据异常等），值得重试
    """
    outcome: str
    message: str = ""
    output_file: Optional[str] = None
    comment_id: Optional[str] = None
    # 服务端返回的弹幕数（本地过滤前），判断「有没有弹幕」只能用这个，
    # 不能用本地 .ass 行数——后者掺了 onlyFromBili 之类的本地过滤
    danmu_count: int = 0

    @property
    def is_ok(self) -> bool:
        return self.outcome == "ok"


class DanmuUnresolvable(Exception):
    """
    本次无法判定弹幕归属，且重试不会改变结果（如 .strm 文件缺少 TMDB ID）。

    与 DanmuThrottled 的区别：限流是暂时的，稍后重试有意义；这里是持久的，
    条件不变就永远是同一个结果，因此不得进入重试列表。两者都不等于「没有弹幕」。
    """

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


class _TokenBucket:
    """
    进程级令牌桶。所有弹弹API请求共用一个桶，刮削线程在此排队，
    这样限流与刮削并发数解耦——本地的 ffprobe/MD5/合并字幕不该被限流拖慢。
    """

    def __init__(self, rate_per_minute: float, burst: int):
        self._rate = rate_per_minute / 60.0
        self._burst = float(burst)
        self._tokens = float(burst)
        self._updated = time.monotonic()
        self._lock = threading.Lock()

    def _take_locked(self) -> float:
        """取一个令牌，成功返回0，否则返回需要等待的秒数"""
        now = time.monotonic()
        self._tokens = min(self._burst, self._tokens + (now - self._updated) * self._rate)
        self._updated = now
        if self._tokens >= 1:
            self._tokens -= 1
            return 0.0
        return (1 - self._tokens) / self._rate

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        取一个令牌
        :param timeout: 最长等待秒数，None表示一直等（后台刮削用）；
                        UI请求应传入较小值以便快速失败
        :return: 是否取到令牌
        """
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            with self._lock:
                wait = self._take_locked()
            if wait <= 0:
                return True
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                wait = min(wait, remaining)
            time.sleep(wait)


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
    # Version suffix is filled in by set_client_version() from the plugin class,
    # so the plugin version lives in exactly one place
    HEADERS = {
        'Accept': 'application/json',
        "User-Agent": "Moviepilot/plugins"
    }
    MANUAL_MATCH_FILE = ".dandan.anime.json"
    # (connect, read) timeout for all dandan API calls; without this a hung
    # request blocks a worker thread forever and stalls batch scraping
    TIMEOUT = (10, 60)

    # 客户端限速：与服务端搜索类限速对齐（30 请求/分钟）。
    # 服务端契约：nginx 限速返回 429 且不带 Retry-After；应用层日预算超额
    # 返回 429 带 Retry-After；配额熔断返回 503 带 Retry-After。
    RATE_PER_MINUTE = 30
    RATE_BURST = 5
    # 服务端没给 Retry-After 时的兜底退避
    DEFAULT_RETRY_AFTER = 60
    MAX_RETRY_AFTER = 3600
    # 闸门关闭时长在此值以内就地等待，超过则让调用方中止本批
    GATE_WAIT_MAX = 120

    _bucket = _TokenBucket(RATE_PER_MINUTE, RATE_BURST)
    _session: Optional[requests.Session] = None
    _session_lock = threading.Lock()
    # 进程级限流闸门：任一线程撞到429/503即关闸，其余线程发请求前先看闸
    _gate_lock = threading.Lock()
    _blocked_until = 0.0

    @classmethod
    def _get_session(cls) -> requests.Session:
        """复用连接，避免每次请求都重新握手TLS"""
        if cls._session is None:
            with cls._session_lock:
                if cls._session is None:
                    cls._session = requests.Session()
        return cls._session

    @classmethod
    def blocked_seconds(cls) -> float:
        """闸门剩余关闭时长，0表示当前可以发请求"""
        with cls._gate_lock:
            return max(0.0, cls._blocked_until - time.monotonic())

    @classmethod
    def _close_gate(cls, retry_after: float) -> None:
        with cls._gate_lock:
            until = time.monotonic() + retry_after
            if until > cls._blocked_until:
                cls._blocked_until = until

    @classmethod
    def reset_gate(cls) -> None:
        """插件重新加载时清空闸门"""
        with cls._gate_lock:
            cls._blocked_until = 0.0

    @classmethod
    def _parse_retry_after(cls, response: requests.Response) -> float:
        """
        解析 Retry-After。nginx 限速那层不带这个头，读不到用兜底值。
        """
        raw = response.headers.get("Retry-After")
        if raw:
            try:
                return max(1.0, min(float(raw), cls.MAX_RETRY_AFTER))
            except (TypeError, ValueError):
                # HTTP-date 形式的 Retry-After 不常见，直接走兜底
                logger.debug(f"无法解析Retry-After: {raw}")
        return float(cls.DEFAULT_RETRY_AFTER)

    @classmethod
    def _wait_for_gate(cls, acquire_timeout: Optional[float]) -> None:
        """
        等待闸门打开。关闭时长超过 GATE_WAIT_MAX（或超过调用方允许的等待时间）
        时抛出 DanmuThrottled，由调用方决定中止。
        """
        blocked = cls.blocked_seconds()
        if blocked <= 0:
            return
        limit = cls.GATE_WAIT_MAX if acquire_timeout is None else min(cls.GATE_WAIT_MAX, acquire_timeout)
        if blocked > limit:
            raise DanmuThrottled(blocked)
        logger.info(f"弹弹API限流中，等待 {blocked:.0f} 秒后继续")
        time.sleep(blocked)

    @classmethod
    def _request(cls, method: str, url: str, *, json_body: Optional[Dict] = None,
                 params: Optional[Dict] = None,
                 acquire_timeout: Optional[float] = None) -> Optional[requests.Response]:
        """
        所有弹弹API请求的唯一入口：闸门 -> 令牌桶 -> 发送 -> 限流判定。
        :param method: HTTP方法
        :param url: 完整URL
        :param json_body: POST的JSON体
        :param params: 查询参数
        :param acquire_timeout: 最长等待秒数，None表示后台刮削可一直等；
                                UI请求应传入较小值以便快速失败
        :return: 响应对象；网络异常返回None
        :raises DanmuThrottled: 服务端限流/熔断，或本地令牌等待超时
        """
        # 最多两次尝试：首次撞到短时限流时，等闸门开了再补一次
        for attempt in range(2):
            cls._wait_for_gate(acquire_timeout)
            if not cls._bucket.acquire(timeout=acquire_timeout):
                raise DanmuThrottled(60.0 / cls.RATE_PER_MINUTE)
            try:
                response = cls._get_session().request(
                    method, url, json=json_body, params=params,
                    headers=cls.HEADERS, timeout=cls.TIMEOUT
                )
            except requests.RequestException as e:
                logger.error(f"请求弹弹API失败 {url}: {e}")
                return None

            if response.status_code not in (429, 503):
                return response

            retry_after = cls._parse_retry_after(response)
            cls._close_gate(retry_after)
            logger.warning(
                f"弹弹API返回 {response.status_code}，{retry_after:.0f} 秒内暂停请求: {url}"
            )
            if attempt == 0 and retry_after <= cls.GATE_WAIT_MAX:
                continue
            raise DanmuThrottled(retry_after, response.status_code)

        # 两次尝试都被限流
        raise DanmuThrottled(cls.blocked_seconds() or cls.DEFAULT_RETRY_AFTER)

    @classmethod
    def set_client_version(cls, version: Optional[str]) -> None:
        """
        Sync the API User-Agent with the plugin version so it is declared in
        one place only (the plugin class) instead of being kept in step by hand.
        """
        if not version:
            return
        cls.HEADERS = {**cls.HEADERS, "User-Agent": f"Moviepilot/plugins {version}"}

    @classmethod
    def _manual_file_path(cls, directory: str) -> str:
        return os.path.join(directory, cls.MANUAL_MATCH_FILE)

    # 弹幕ID编码：episodeId = animeId * 10000 + 集内序号。
    # 序号 0..8999 是正片（第0集是合法的放送前特番/序章）；
    # 9000-9099=S特别篇、9100-9199=C(OP/ED)、9400-9499=O其他；
    # >=10000 会进位到 animeId+1，也就是**另一部作品**。
    # 边界钉在编码规则上，不能用「合理集数」之类的启发式——真实长番集号已达
    # 3000+ 且还在涨，任何经验阈值迟早会静默拒掉真实集数。
    MAX_REGULAR_EPISODE = 8999

    @classmethod
    def _normalize_episode(cls, episode: Optional[int]) -> Optional[int]:
        """
        校验集号能否用于拼接正片弹幕ID。
        :return: 有效集号；无法判定时返回None，由调用方回退常规匹配。
                 **绝不夹取**——夹取会把「无法判定」变成「自信地给了个错答案」。
        """
        # 无集数信息（电影、单条目作品）按第1集处理，这是弹弹play的编码约定
        if episode is None or episode == "":
            return 1
        try:
            value = int(episode)
        except (TypeError, ValueError):
            logger.warning(f"集数无法解析，放弃拼接弹幕ID: {episode}")
            return None
        if value < 0 or value > cls.MAX_REGULAR_EPISODE:
            logger.warning(
                f"集号 {value} 超出正片编码范围 0-{cls.MAX_REGULAR_EPISODE}，"
                f"放弃拼接弹幕ID（>=9000 会落进特典段，>=10000 会指向另一部作品）"
            )
            return None
        return value

    @staticmethod
    def _apply_episode_offset(episode: Optional[int], offset: Any) -> Optional[int]:
        """
        Shift local episode number to the dandanplay-side numbering.
        Local episode + offset = dandanplay episode, clamped to >= 0
        (episode 0 is a legitimate pre-broadcast special, not an error).
        """
        try:
            offset_int = int(offset)
        except (TypeError, ValueError):
            return episode
        if offset_int == 0:
            return episode
        try:
            episode_int = int(episode)
        except (TypeError, ValueError):
            episode_int = 1
        return max(0, episode_int + offset_int)

    @classmethod
    def _compose_comment_id(cls, anime_id: Any, episode: Optional[int]) -> Optional[str]:
        try:
            anime_id_int = int(anime_id)
        except (TypeError, ValueError):
            return None
        episode_int = cls._normalize_episode(episode)
        if episode_int is None:
            return None
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

    _ffmpeg_available: Optional[bool] = None
    _ffmpeg_lock = threading.Lock()

    @classmethod
    def ffmpeg_available(cls) -> bool:
        """
        ffmpeg 是否可用，只探测一次。
        它决定要不要做哈希匹配，而哈希匹配的前置开销（读 16MB、spawn 进程）
        是**每个文件**都要付的——没有 ffmpeg 时这些开销全是白费。
        """
        if cls._ffmpeg_available is None:
            with cls._ffmpeg_lock:
                if cls._ffmpeg_available is None:
                    cls._ffmpeg_available = shutil.which("ffmpeg") is not None
                    if not cls._ffmpeg_available:
                        _warn_once(
                            "ffmpeg-missing",
                            "未找到 ffmpeg，无法获取视频时长，哈希匹配将被跳过，"
                            "改为仅使用 TMDB 匹配。这不影响已收录内容的刮削，"
                            "但会降低命中率；如需恢复请在容器/主机中安装 ffmpeg 并确保在 PATH 中"
                        )
        return cls._ffmpeg_available

    @classmethod
    def reset_environment_probe(cls) -> None:
        """插件重载时重新探测——用户可能刚装上 ffmpeg"""
        with cls._ffmpeg_lock:
            cls._ffmpeg_available = None

    @staticmethod
    def get_video_duration(file_path: str) -> Optional[float]:
        try:
            try:
                process = subprocess.Popen(
                    ['ffmpeg', '-i', file_path],
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE
                )
            except FileNotFoundError:
                # 这是环境问题而不是文件问题，而且会影响每一个文件——
                # 只说一次，说清楚怎么办
                _warn_once(
                    "ffmpeg-missing",
                    "未找到 ffmpeg，无法获取视频时长。哈希匹配将被跳过，"
                    "只能依赖 TMDB 匹配；请确认容器/主机中已安装 ffmpeg 并在 PATH 中"
                )
                return None
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

    # 特典编码分段：9000-9099=S特别篇、9100-9199=C(OP/ED)、9400-9499=O其他。
    # 未观测到 92xx/93xx，遇到就当未知、不猜。
    SPECIAL_SEGMENTS = ((9000, "S"), (9100, "C"), (9400, "O"))

    @classmethod
    def decode_episode_id(cls, episode_id: Any) -> Optional[Dict[str, Any]]:
        """
        从 episodeId 还原集号。整季查询的响应里没有 episodeNumber 字段，
        只能靠编码规则 `episodeId = animeId * 10000 + 集内序号` 反推。
        :return: {"kind": regular/S/C/O/unknown, "number": int}；无法解析返回None
        """
        try:
            value = int(episode_id)
        except (TypeError, ValueError):
            return None
        lo = value % 10000
        if lo <= cls.MAX_REGULAR_EPISODE:
            # 0 是合法的第0集（放送前特番/序章），不是异常
            return {"kind": "regular", "number": lo}
        for base, kind in cls.SPECIAL_SEGMENTS:
            if base <= lo < base + 100:
                return {"kind": kind, "number": lo - base}
        return {"kind": "unknown", "number": None}

    @classmethod
    def _parse_series_entry(cls, anime: Dict[str, Any]) -> Dict[str, Any]:
        """
        把整季查询里的一个条目整理成本地结构。
        正片集号来自 episodeId 解码；若解码出的顺序与数组顺序矛盾，
        退回按数组顺序编号（服务端只验证过两部剧，留个防御）。
        """
        episodes = []
        for item in anime.get("episodes") or []:
            decoded = cls.decode_episode_id(item.get("episodeId"))
            if not decoded:
                continue
            episodes.append({
                "episodeId": str(item.get("episodeId")),
                "title": item.get("episodeTitle"),
                "kind": decoded["kind"],
                "number": decoded["number"],
            })

        regulars = [e for e in episodes if e["kind"] == "regular"]
        numbers = [e["number"] for e in regulars]
        if numbers != sorted(numbers):
            logger.warning(
                f"条目 {anime.get('animeId')} 解码出的集号与列表顺序矛盾，退回按顺序编号"
            )
            for index, ep in enumerate(regulars, start=1):
                ep["number"] = index

        return {
            "animeId": anime.get("animeId"),
            "animeTitle": anime.get("animeTitle"),
            "episodes": episodes,
            # 推导季偏移时只能数正片：特典混在里面会让整季错位
            "regularCount": len(regulars),
        }

    @classmethod
    def search_series(cls, tmdb_id: int, tmdb_id_type: int = 0) -> "SeriesLookup":
        """
        整季查询：省略 episode 参数，一次拿到该作品在弹弹play 的全部条目
        及各自完整剧集列表。

        四种结局必须分开，合并任意两个都会出问题：
          ok        —— 拿到完整列表，可据此零请求定位
          absent    —— 空列表，确认无收录（权威结论）
          truncated —— hasMore 置位。服务端在总集数约 201 处截断，**条目和集数
                       一起丢**，此时套偏移公式会静默错位几百集（实测火影疾风传
                       条目内第1集其实是 TMDB 第221集）。必须整批作废走逐集。
          unknown   —— 请求失败，什么都不能推断，尤其不能缓存
        :raises DanmuThrottled: 被限流
        """
        try:
            response = DanmuAPI._request(
                "POST", f"{cls.BASE_URL}/search/tmdb",
                json_body={"tmdb_id": tmdb_id, "tmdb_id_type": tmdb_id_type}
            )
            if response is None or response.status_code != 200:
                return SeriesLookup("unknown")
            result = response.json()
            if not result.get("success"):
                return SeriesLookup("unknown")
            if result.get("hasMore"):
                logger.info(
                    f"整季结果被截断（tmdb={tmdb_id}，长番超出服务端返回上限），"
                    f"该作品改走逐集匹配"
                )
                return SeriesLookup("truncated")
            entries = [cls._parse_series_entry(a) for a in (result.get("animes") or [])]
            return SeriesLookup("ok" if entries else "absent", entries)
        except DanmuThrottled:
            raise
        except Exception as e:
            logger.error(f"整季查询失败 tmdb={tmdb_id}: {e}")
            return SeriesLookup("unknown")

    @staticmethod
    def _find_in_entry(entry: Dict[str, Any], kind: str, number: int) -> Optional[str]:
        for ep in entry.get("episodes") or []:
            if ep["kind"] == kind and ep["number"] == number:
                return ep["episodeId"]
        return None

    @classmethod
    def locate_episode(cls, series: List[Dict[str, Any]], season: Optional[int],
                       episode: Optional[int]) -> Optional[str]:
        """
        在整季结果里定位本地文件对应的 episodeId。

        弹弹play 按「条目」组织（通常一季一个条目），每个条目的集号都从 1 开始，
        所以必须有季号才能定位。返回 None 表示这一集确实不在列表里——
        这是**确定性结论**，不需要再发请求去问。

        :param series: search_series 的结果
        :param season: 本地季号（TMDB 的 Season 0 表示特典）
        :param episode: 本地集号
        """
        if not series:
            return None
        # 电影或无集数信息：取正片那一集。电影条目里往往混着十几段 S 类花絮
        # （访谈、首映、制作特辑），取 episodes[0] 只是碰巧正片排在第一位，
        # 顺序一变就会给用户放一段花絮的弹幕
        if episode is None:
            for entry in series:
                for ep in entry.get("episodes") or []:
                    if ep["kind"] == "regular":
                        return ep["episodeId"]
            return None

        # TMDB 的 Season 0 是特典。弹弹play 把特典细分成 S/C/O 三段，
        # 而 Season 0 是扁平的——默认映射到 S 段（特别篇），
        # C 段是 OP/ED、O 段多为剧场版，很少作为独立文件进媒体库
        if season == 0:
            for entry in series:
                found = cls._find_in_entry(entry, "S", episode)
                if found:
                    return found
            return None

        index = (season - 1) if season else 0
        # 1) 季号能对上条目，且该条目里有这一集
        if 0 <= index < len(series):
            found = cls._find_in_entry(series[index], "regular", episode)
            if found:
                return found

        # 2) TMDB 连续计数、弹弹按季重置：减掉前面各季的**正片**数量。
        #    只数正片是关键——特典混进来会让整季偏移多算，且不会报错
        if 0 <= index < len(series):
            consumed = sum(e.get("regularCount", 0) for e in series[:index])
            found = cls._find_in_entry(series[index], "regular", episode - consumed)
            if found:
                logger.info(
                    f"按连续集数推导偏移 -{consumed}：本地第 {episode} 集 "
                    f"→ 条目内第 {episode - consumed} 集"
                )
                return found

        # 3) 只有一个条目时，季号可能不可靠，直接按集号找一次
        if len(series) == 1:
            return cls._find_in_entry(series[0], "regular", episode)
        return None

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
            response = DanmuAPI._request("POST", url, json_body=data)
            if response is not None and response.status_code == 200:
                result = response.json()
                if result.get("success") and not result.get("hasMore"):
                    animes = result.get("animes", [])
                    if animes and len(animes) > 0:
                        episodes = animes[0].get("episodes", [])
                        if episodes and len(episodes) > 0:
                            return str(episodes[0].get("episodeId"))
            return None
        except DanmuThrottled:
            # 被限流不等于没有内容，必须原样抛出让上层区分
            raise
        except Exception as e:
            logger.error(f"使用TMDB ID搜索弹幕失败: {e}")
            return None

    @staticmethod
    def get_comment_id(file_path: str, use_tmdb_id: bool = False, tmdb_id: Optional[int] = None,
                       episode: Optional[int] = None, tmdb_id_type: int = 0) -> Optional[str]:
        """
        获取弹幕ID。
        注意这一层没有缓存参数：服务端的 /match 与 /search/tmdb 都不接受 TTL，
        ID 层的缓存应当做在客户端（本地刮削状态库）。
        :param file_path: 视频文件路径
        :param use_tmdb_id: 是否使用TMDB ID
        :param tmdb_id: TMDB ID
        :param episode: 集数
        :param tmdb_id_type: TMDB ID类型，0=电视剧，1=电影
        :return: 弹幕ID
        """
        try:
            # 手动匹配（含目录级）由插件层统一解析后经 manual_comment_id 传入，
            # 这里只负责向服务端查询，不再自己读盘

            # 检查是否为.strm文件
            if StrmProcessor.is_strm_file(file_path):
                logger.info(f"检测到.strm文件: {file_path}")
                # 读取.strm文件内容
                strm_url = StrmProcessor.get_strm_url(file_path)
                if strm_url:
                    logger.info(f"STRM文件指向: {strm_url}")

                # .strm 文件没有本地视频数据，无法走 hash 匹配，只能靠 TMDB ID
                if tmdb_id is None:
                    # 零请求就能得出的结论：条件不变，重试多少次都是同样结果
                    raise DanmuUnresolvable(
                        f".strm文件缺少TMDB ID，无法匹配弹幕（请检查媒体识别或开启「使用TMDB ID」）: {file_path}"
                    )

                logger.info(f"为.strm文件使用TMDB ID匹配: {tmdb_id}")
                return DanmuAPI.search_by_tmdb_id(tmdb_id, episode, tmdb_id_type)

            # 普通视频文件的处理逻辑。
            # /match 靠 文件名+哈希+大小+时长 四要素识别，缺任何一项都必然失败——
            # 「算不出来」和「值就是这个」不是一回事，不能拿占位值去发请求。
            # 没有 ffmpeg 时时长一定拿不到，所以连 16MB 哈希都不必算，直接走 TMDB
            missing = []
            # ffmpeg 缺失已由 ffmpeg_available() 给出完整诊断（是什么/后果/怎么办），
            # 这里不再重复说一遍同一个根因
            ffmpeg_missing = not DanmuAPI.ffmpeg_available()
            if ffmpeg_missing:
                logger.debug(f"未安装 ffmpeg，跳过哈希匹配: {file_path}")
            else:
                file_name = os.path.basename(file_path)
                file_size = DanmuAPI.get_file_size(file_path)
                file_hash = DanmuAPI.calculate_md5_of_first_16MB(file_path)
                duration = DanmuAPI.get_video_duration(file_path)
                if not file_hash:
                    missing.append("文件哈希")
                if not file_size:
                    missing.append("文件大小")
                if duration is None:
                    missing.append("视频时长（该文件无法解析）")

            if missing and not ffmpeg_missing:
                reason = "、".join(missing)
                # 同一个原因只醒目地说一次；逐文件的细节留给 debug
                _warn_once(
                    f"match-missing:{reason}",
                    f"缺少 {reason}，跳过哈希匹配，改由 TMDB 匹配。"
                    f"首个受影响文件: {file_path}"
                )
                logger.debug(f"跳过哈希匹配，缺少 {reason}: {file_path}")

            if not missing and not ffmpeg_missing:
                video_info = VideoInfo(
                    file_name=file_name,
                    file_hash=file_hash,
                    file_size=file_size,
                    video_duration=int(duration)
                )
                response = DanmuAPI._request(
                    "POST", f"{DanmuAPI.BASE_URL}/match",
                    json_body=video_info.__dict__
                )
                if response is not None and response.status_code == 200:
                    result = response.json()
                    if result.get("isMatched") and result.get("matches"):
                        return str(result["matches"][0]["episodeId"])

            # 如果使用TMDB ID且提供了TMDB ID，尝试使用TMDB ID匹配
            if use_tmdb_id and tmdb_id is not None:
                comment_id = DanmuAPI.search_by_tmdb_id(tmdb_id, episode, tmdb_id_type)
                if comment_id:
                    return comment_id

            return None
        except (DanmuThrottled, DanmuUnresolvable):
            raise
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
    def search_anime(cls, keyword: str, anime_type: Optional[str] = None,
                     acquire_timeout: Optional[float] = None) -> Dict:
        """
        搜索弹弹番剧（UI手动匹配用）
        :param keyword: 搜索关键字
        :param anime_type: 作品类型，all或空表示不限
        :param acquire_timeout: 限速等待上限，UI调用应传入较小值以便快速失败
        :return: 服务端返回的JSON
        :raises DanmuThrottled: 被限流
        :raises RuntimeError: HTTP错误或网络异常
        """
        params = {"keyword": keyword}
        if anime_type and anime_type != "all":
            params["type"] = anime_type
        response = cls._request("GET", f"{cls.BASE_URL}/search/anime",
                                params=params, acquire_timeout=acquire_timeout)
        if response is None:
            raise RuntimeError("网络异常，请稍后再试")
        if response.status_code != 200:
            logger.error(f"搜索弹弹失败，HTTP {response.status_code}: {response.text}")
            raise RuntimeError(f"搜索失败: HTTP {response.status_code}")
        return response.json()

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
            response = cls._request("GET", url)
            if response is None:
                return None
            if response.status_code == 200:
                return response.json()
            logger.error(f"获取弹幕失败: {response.text}")
            return None
        except DanmuThrottled:
            raise
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
        dropped_full = 0

        logger.info(f"{output_file} - 共匹配到{len(comments)}条弹幕。")

        with open(output_file, 'w', encoding='utf-8') as f:
            cls.write_ass_head(f, width, height, fontface, fontsize, alpha, styleid)

            for comment in comments:
                try:
                    p = str(comment.get('p', '')).split(',')
                    if len(p) < 3:
                        logger.warning(f"弹幕数据格式不正确: {comment}")
                        continue

                    timeline = float(p[0])
                    pos = int(p[1])
                    color = int(p[2])
                    text = comment.get('m', '')

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
                            dropped_full += 1
                            continue  # 全部轨道占用，跳过避免重叠
                        scrolling_tracks[track_id] = timeline + leave_time
                        initial_y = (track_id - 1) * fontsize + 10
                        styles = f'\\move({width}, {initial_y}, {-len(text)*fontsize}, {initial_y})'
                    elif pos == 4:  # 底部弹幕
                        track_id = cls.find_non_overlapping_track(bottom_tracks, timeline, max_tracks)
                        if track_id is None:
                            dropped_full += 1
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
                            dropped_full += 1
                            continue  # 全部轨道占用，跳过避免重叠
                        top_tracks[track_id] = timeline + duration
                        styles = f'\\an8\\pos({width/2}, {50 + (track_id - 1) * fontsize})'
                    else:
                        styles = f'\\move(0, 0, {width}, 0)'

                    f.write(f'Dialogue: 0,{start_time},{end_time},{styleid},,0,0,0,,{{\\c{color_hex}{styles}}}{text}\n')
                except Exception as e:
                    logger.error(f"处理弹幕数据失败: {e}, 弹幕数据: {comment}")
                    continue

            if dropped_full:
                logger.info(
                    f"{dropped_full}/{len(comments)} 条弹幕因 {max_tracks} 条轨道全部占用被丢弃，"
                    f"可减小字体或扩大弹幕区域"
                )
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
    def _matches_video_name(sub_name: str, video_stem: str) -> bool:
        """
        判断字幕文件是否属于该视频。
        名称需与视频名完全相同，或以「视频名 + 非字母数字分隔符」开头，
        否则 Ep1 会误命中 Ep10.zh.ass。
        :param sub_name: 字幕文件名（不含目录）
        :param video_stem: 视频文件名（不含扩展名）
        """
        stem = os.path.splitext(sub_name)[0]
        if stem == video_stem:
            return True
        if not stem.startswith(video_stem):
            return False
        return not stem[len(video_stem)].isalnum()

    @staticmethod
    def find_subtitle_file(file_path: str) -> Optional[str]:
        video_dir = os.path.dirname(file_path)
        video_stem = os.path.splitext(os.path.basename(file_path))[0]
        ass_candidates = []
        srt_candidates = []
        for root, _, files in os.walk(video_dir):
            for file in files:
                # 跳过本插件产物（.danmu.ass 与 .withDanmu.ass）
                if 'danmu' in file.lower():
                    continue
                if not SubtitleProcessor._matches_video_name(file, video_stem):
                    continue
                full_path = os.path.join(root, file)
                # 同目录字幕优先于子目录（如 Subs/），同级则按文件名排序保证结果稳定
                candidate = (0 if root == video_dir else 1, file, full_path)
                if file.endswith(('.ass', '.ssa')):
                    ass_candidates.append(candidate)
                elif file.endswith('.srt'):
                    srt_candidates.append(candidate)
        # Prefer .ass/.ssa over .srt for richer style information
        for candidates in (ass_candidates, srt_candidates):
            if candidates:
                chosen = min(candidates)[2]
                logger.info(f"找到字幕文件 - {chosen}")
                return chosen
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

def _comment_fields(comment: Any) -> List[str]:
    """
    取出弹幕的p字段分量，格式为 时间,模式,颜色,用户
    """
    if not isinstance(comment, dict):
        return []
    return str(comment.get('p', '')).split(',')


def _comment_timeline(comment: Any) -> float:
    """
    排序用的弹幕时间，解析失败按0处理，避免单条脏数据让整次刮削失败
    """
    fields = _comment_fields(comment)
    if not fields:
        return 0.0
    try:
        return float(fields[0])
    except (TypeError, ValueError):
        return 0.0


def _is_bili_comment(comment: Any) -> bool:
    """
    判断弹幕是否来自B站（用户字段带[BiliBili]标记）
    """
    fields = _comment_fields(comment)
    return len(fields) > 3 and '[BiliBili]' in fields[3]


def _prefer_bili_comments(comments: List[Dict], min_count: int) -> List[Dict]:
    """
    优先使用B站弹幕，B站弹幕不足时回退全部来源。

    实测绝大多数剧集根本没有B站来源的弹幕，若按「仅B站」严格过滤，
    这些文件会写出空弹幕并反复重试，而重试永远改变不了结果。
    回退只在严格模式下本来就拿不到弹幕时触发，所以不会让任何人变差。
    :param comments: 全部来源的弹幕
    :param min_count: B站弹幕低于此数量即视为不足（复用最小弹幕数要求）
    """
    bili_comments = [comment for comment in comments if _is_bili_comment(comment)]
    if len(bili_comments) >= min_count:
        logger.info(f"使用B站弹幕 {len(bili_comments)} 条（全部来源 {len(comments)} 条）")
        return bili_comments
    logger.info(
        f"B站弹幕仅 {len(bili_comments)} 条，少于 {min_count} 条，"
        f"回退使用全部来源 {len(comments)} 条"
    )
    return comments


def danmu_generator(file_path: str, width: int = 1920, height: int = 1080,
                   fontface: str = 'Arial', fontsize: float = 50,
                   alpha: float = 0.8, duration: float = 6, onlyFromBili: bool = False,
                   use_tmdb_id: bool = False, tmdb_id: Optional[int] = None,
                   episode: Optional[int] = None, cache_ttl: Optional[int] = None,
                   screen_area: str = 'full', manual_comment_id: Optional[str] = None,
                   tmdb_id_type: int = 0, min_danmu_count: int = 100) -> DanmuResult:
    try:
        comment_id = manual_comment_id or DanmuAPI.get_comment_id(
            file_path, use_tmdb_id, tmdb_id, episode, tmdb_id_type
        )
        if not comment_id:
            # 问过了，弹弹play 没有这个内容。这不是失败，重试也不会变
            logger.info(f"弹弹play未收录该内容 - {file_path}")
            return DanmuResult("absent", message="弹弹play未收录该内容")

        comments_data = DanmuAPI.get_comments(comment_id, cache_ttl=cache_ttl)
        if not comments_data:
            return DanmuResult("failed", message="未获取到弹幕数据", comment_id=comment_id)

        raw_comments = comments_data.get("comments")
        if not isinstance(raw_comments, list):
            logger.warning(f"弹幕数据格式异常，缺少comments列表 - {file_path}")
            return DanmuResult("failed", message="弹幕数据格式异常", comment_id=comment_id)

        comments = sorted(raw_comments, key=_comment_timeline)
        server_count = len(comments)

        if server_count == 0:
            # 条目是有的，只是还没有人发弹幕——新番常见，之后可能会有
            logger.info(f"该内容已收录但暂时没有弹幕 - {file_path}")
            return DanmuResult("empty", message="已收录，但暂时没有弹幕",
                               comment_id=comment_id)

        # 优先B站弹幕（不足则回退全部来源）
        if onlyFromBili:
            comments = _prefer_bili_comments(comments, min_danmu_count)

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

        return DanmuResult("ok", output_file=output_file,
                           comment_id=comment_id, danmu_count=server_count)

    except (DanmuThrottled, DanmuUnresolvable):
        # 交由插件层处理：既不算失败，也不进重试列表
        raise
    except Exception as e:
        logger.error(f"生成弹幕失败: {e}")
        return DanmuResult("failed", message=f"生成弹幕失败: {str(e)}")
