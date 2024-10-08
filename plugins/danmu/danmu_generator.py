import chardet
import requests, os, re, hashlib
import subprocess, json
from app.log import logger

def calculate_md5_of_first_16MB(file_path):
    # 创建一个新的MD5哈希对象
    md5 = hashlib.md5()
    
    # 16MB的大小（以字节为单位）
    size_16MB = 16 * 1024 * 1024
    
    # 打开文件，并读取前16MB数据
    with open(file_path, 'rb') as f:
        data = f.read(size_16MB)
        md5.update(data)
    
    # 返回MD5哈希值的十六进制表示
    return md5.hexdigest()

def get_video_duration(file_path):
    # 构建ffmpeg命令
    cmd = ['ffmpeg', '-i', file_path]

    try:
        # 调用ffmpeg命令并捕获输出
        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout, stderr = process.communicate()

        # 尝试以utf-8解码
        try:
            # 尝试使用 'ignore' 模式忽略解码错误
            stderr = stderr.decode('utf-8', errors='ignore')
        except UnicodeDecodeError as e:
            logger.warning(f"utf-8 解码失败：{e}. 尝试使用替换模式。")
            stderr = stderr.decode('utf-8', errors='replace')

        # 使用正则表达式解析视频文件的时长
        duration_match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", stderr)
        if duration_match:
            hours = int(duration_match.group(1))
            minutes = int(duration_match.group(2))
            seconds = float(duration_match.group(3))

            # 将时长转换为秒
            total_seconds = hours * 3600 + minutes * 60 + seconds
            return total_seconds
        else:
            logger.error(f"无法找到视频时长信息 - {file_path}")
            return None
    except FileNotFoundError:
        logger.error("ffmpeg 工具没有找到，请确保已安装并正确配置路径。")
    except Exception as e:
        logger.error(f"处理文件 {file_path} 时出错: {e}")

    return None
    
def get_file_size(file_path):
    # 获取文件的大小，单位为字节
    file_size_in_bytes = os.path.getsize(file_path)
    return file_size_in_bytes

    
def get_comment_ID(file_path):
    url = f'https://api.dandanplay.net/api/v2/match'
    headers = {
        'Accept': 'application/json',
        "User-Agent": "Moviepilot/plugins 1.1.0"
    }
    duration = int(get_video_duration(file_path))
    hash = calculate_md5_of_first_16MB(file_path)
    name = os.path.basename(file_path)
    try:
        size = get_file_size(file_path)
        duration = int(get_video_duration(file_path))
        info = {
            "fileName": name,
            "fileHash": hash,
            "fileSize": size,
            "videoDuration": duration,
            "matchMode": "hashAndFileName"
        }
    except:
        logger.error('获取文件信息失败')
        info = {
            "fileName": name,
            "fileHash": hash,
            "fileSize": 0,
            "videoDuration": 0,
            "matchMode": "hashAndFileName"
        }
    response = requests.post(url, headers=headers, json=info)
    if response.status_code == 200:
        if response.json()['isMatched']:
            return response.json()['matches'][0]['episodeId']
        else:
            if len(response.json()['matches']) == 0:
                logger.error('未找到弹幕可能匹配 - ' + file_path)
                return None
            logger.info('尝试从nfo文件获取标题 - ' + file_path)
            title = get_title_from_nfo(file_path)
            if not title:
                logger.info('未找到标题 跳过 - ' + file_path)
                return None
            # 尝试从标题匹配
            for match in response.json()['matches']:
                episodeTitle = match['episodeTitle']
                # 去除 第x话
                # 稍微严格一点 不用contains
                episodeTitle = re.sub(r'第\d+话 ', '', episodeTitle)
                if episodeTitle == title:
                    logger.info('匹配成功 - ' + file_path)
                    return match['episodeId']
            logger.info('未找到匹配，跳过 - ' + file_path)
            return None
    else:
        logger.error("获取弹幕ID失败 %s" % response.text)
        return None
   
def get_title_from_nfo(file_path):
    # 尝试读取nfo文件
    logger.info('尝试读取nfo文件 - ' + file_path)
    nfo_file = os.path.splitext(file_path)[0] + '.nfo'
    try:
        with open(nfo_file) as f:
            nfo_content = f.read()
            try:
                title = re.search(r'<title>(.*)</title>', nfo_content).group(1)
                logger.info('从nfo文件中获取标题 - ' + title)
                return title
            except:
                logger.error('未找到标题信息')
                return None
    except:
        logger.error('未找到nfo文件')
        return None
        
def get_comments(comment_id):
    url = f'https://api.dandanplay.net/api/v2/comment/{comment_id}?withRelated=true'
    headers = {
        'Accept': 'application/json',
        "User-Agent": "Moviepilot/plugins 1.1.0"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error("获取弹幕失败 %s" % response.text)
        return None

def convert_timestamp(timestamp):
    timestamp = round(timestamp * 100.0)
    hour, minute = divmod(timestamp, 360000)
    minute, second = divmod(minute, 6000)
    second, centsecond = divmod(second, 100)
    return '%d:%02d:%02d.%02d' % (int(hour), int(minute), int(second), int(centsecond))

def write_ass_head(f, width, height, fontface, fontsize, alpha, styleid):
    f.write(
'''[Script Info]
; Script generated by Hankun 
; Super thanks to https://github.com/m13253/danmaku2ass and https://www.dandanplay.com/
Script Updated By: MoviePilot Danmu Plugin https://github.com/HankunYu/MoviePilot-Plugins
ScriptType: v4.00+
PlayResX: %(width)d
PlayResY: %(height)d
Aspect Ratio: %(width)d:%(height)d
Collisions: Normal
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: %(styleid)s, %(fontface)s, %(fontsize).0f, &H%(alpha)02XFFFFFF, &H%(alpha)02XFFFFFF, &H%(alpha)02X000000, &H%(alpha)02X000000, 0, 0, 0, 0, 100, 100, 0.00, 0.00, 1, %(outline).0f, 0, 7, 0, 0, 0, 0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
''' % {'width': width, 'height': height, 'fontface': fontface, 'fontsize': fontsize, 'alpha': 255 - round(alpha * 255), 'outline': max(fontsize / 25.0, 1), 'styleid': styleid}
    )

def convert_comments_to_ass(comments, output_file, width=1920, height=1080, fontface='Arial', fontsize=50, alpha=0.8, duration=6):
    styleid = 'Danmu'
    
    def find_non_overlapping_track(tracks, current_time, max_tracks):
        possible_track = 1
        last_time_remain = 100
        for track in range(1, max_tracks + 1):
            if track not in tracks or current_time >= tracks[track]:
                return track
            else:
                time_remain = tracks[track] - current_time
                if time_remain > last_time_remain:
                    possible_track = track
        # 如果所有轨道都满了 返回离弹幕结束最快的轨道
        return possible_track
    
    with open(output_file, 'w', encoding='utf-8-sig') as f:
        write_ass_head(f, width, height, fontface, fontsize, alpha, styleid)
        
        max_tracks = height // fontsize  # Maximum number of tracks that can fit in the screen height
        scrolling_tracks = {}
        top_tracks = {}
        bottom_tracks = {}
        logger.info(f"{output_file} - 共匹配到{len(comments)}条弹幕。")
        for comment in comments:
            p = comment['p'].split(',')
            timeline, pos, color, _ = float(p[0]), int(p[1]), int(p[2]), str(p[3])
            text = comment['m']
            
            start_time = convert_timestamp(timeline)
            end_time = convert_timestamp(timeline + float(duration))  # 默认显示时间为6秒
            
            # 同轨道滚动弹幕之间间隔时间
            gap = 1
            # 计算弹幕的宽度
            text_width = len(text) * fontsize * 0.6  # 粗略估算宽度
            # 计算弹幕尾部离开轨道起始点的时间
            velocity = (width + text_width) / float(duration)
            leave_time = text_width / velocity + gap

            color_hex = '&H{0:06X}'.format(color & 0xFFFFFF)
            styles = ''
            
            if pos == 1:  # 滚动弹幕
                track_id = find_non_overlapping_track(scrolling_tracks, timeline, max_tracks)
                scrolling_tracks[track_id] = timeline + leave_time
                initial_y = (track_id - 1) * fontsize + 10
                styles = f'\\move({width}, {initial_y}, {-len(text)*fontsize}, {initial_y})'
            elif pos == 4:  # 底部弹幕
                track_id = find_non_overlapping_track(bottom_tracks, timeline, max_tracks)
                bottom_tracks[track_id] = timeline + float(duration)
                styles = f'\\an2\\pos({width/2}, {height - 50 - (track_id - 1) * fontsize})'
            elif pos == 5:  # 顶部弹幕
                track_id = find_non_overlapping_track(top_tracks, timeline, max_tracks)
                top_tracks[track_id] = timeline + float(duration)
                styles = f'\\an8\\pos({width/2}, {50 + (track_id - 1) * fontsize})'
            else:
                styles = '\\move({}, {}, {}, {})'.format(0, 0, width, 0)

            f.write(f'Dialogue: 0,{start_time},{end_time},{styleid},,0,0,0,,{{\\c{color_hex}{styles}}}{text}\n')
        logger.info('弹幕生成成功 - ' + output_file)

def sort_comments(comment_data):
    # 提取 comments 列表
    comments = comment_data["comments"]
    
    def extract_time(comment):
      # 提取 p 字段中的时间部分
      p_field = comment['p']
      time_str = p_field.split(',')[0]
      return float(time_str)
    
    # 按照从 p 字段提取的时间进行排序
    return sorted(comments, key=extract_time)

def generate_danmu_ass(comment_ID, file_path, width=1920, height=1080, fontface='Arial', fontsize=50, alpha=0.8, duration=6):
  comments = sort_comments(get_comments(comment_ID))
  output = os.path.splitext(file_path)[0] + '.danmu.ass'
  convert_comments_to_ass(comments, output, width, height, fontface, fontsize, alpha, duration)

# sub1 为弹幕字幕，sub2 为原生字幕
def combine_sub_ass(sub1, sub2) -> bool:
    if not sub1 or not sub2:
        return False
    
    # 读取两个字幕文件的内容
    with open(sub1, 'r', encoding='utf-8-sig') as f:
        sub1_content = f.read()
    with open(sub2, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        file_encoding = result['encoding']
    with open(sub2, 'r', encoding=file_encoding) as f:
        sub2_content = f.read()
        
    # 检查原生字幕格式
    # 如果字幕是ass 或者ssa 格式，ssa格式按照ass处理
    if os.path.splitext(sub2)[1].lower() == '.ass' or os.path.splitext(sub2)[1].lower() == '.ssa':
        sub1ResX = re.search(r"PlayResX:\s*(\d+)", sub1_content)
        sub2ResX = re.search(r"PlayResX:\s*(\d+)", sub2_content)

        # 计算两个字幕的分辨率的比例 （大致
        if not sub1ResX or not sub2ResX:
            fontSizeRatio = 1
        else:
            fontSizeRatio = int(sub1ResX.group(1)) / int(sub2ResX.group(1)) * 0.8

        # 提取原生字幕的样式格式
        format_match = re.search(r"Format:.+", sub2_content)
        if not format_match:
            return False

        format_line = format_match.group()

        style_lines = re.findall(r'Style:.*', sub2_content)
        for i, line in enumerate(style_lines):
            elements = line.split(',')
            if(len(elements) < 3):
              continue
            elements[2] = str(int(float(elements[2]) * fontSizeRatio))  # 修改字体大小
            style_lines[i] = ','.join(elements)

        # 拼接所有样式
        styles_content = '\n'.join(style_lines)

        # 提取原生字幕的内容
        events_start = sub2_content.find('[Events]')
        if events_start == -1:
            return False  # 未找到[Events]

        events_content = sub2_content[events_start + len('[Events]'):].strip()
        
        # 获取合并后sub名字
        output = os.path.splitext(sub2)[0] + ".withDanmu.ass"
        with open(output, 'w', encoding='utf-8-sig') as f:
            # 写入弹幕字幕的内容
            f.write(sub1_content)
            f.write('\n')
            f.write('[V4+ Styles]\n')
            f.write(format_line)
            f.write('\n')
            f.write(styles_content)
            f.write('\n')
            f.write('[Events]\n')
            f.write(events_content)
    
            return True

    elif os.path.splitext(sub2)[1].lower() == '.srt':
        return False
    else:
        return False
        
# 检查文件是否有自带的字幕
def find_subtitle_file(file_path):
    # 遍历文件目录
    filename = os.path.basename(file_path)
    filename = os.path.splitext(filename)[0]
    for root, dirs, files in os.walk(os.path.dirname(file_path)):
        for file in files:
            # 检查文件是否以.srt .ass .ssa结尾，并且不包含'danmu'这个字符串
            if (file.endswith('.srt') or file.endswith('.ass') or file.endswith('.ssa')) and 'danmu' not in file and file.startswith(filename):
                sub2 = os.path.join(root, file)
                logger.info("找到字幕文件 - " + sub2)
                # 返回文件路径
                return sub2
    
    # 如果没有找到符合条件的文件，返回None
    logger.info("没找到字幕文件")
    return None

# 获得视频文件中所有流信息，包括字幕流
def get_video_streams(file_path):
    command = [
        'ffprobe', '-v', 'error', 
        '-print_format', 'json', '-show_format', '-show_streams', file_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if result.returncode != 0:
        return {}
    else:
        return json.loads(result.stdout)
  
# 提取视频文件中的指定字幕流
def extract_subtitles(file_path, output_file, stream_index):
    command = [
        'ffmpeg',
        '-i', file_path,
        '-map', f'0:{stream_index}',
        '-c:s', 'ass',
        output_file
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    return result.returncode == 0

# 提取所有字幕流，并按照字幕名字命名
def try_extract_sub(file_path):
    # 获取视频流信息
    streams_info = get_video_streams(file_path)

    for stream in streams_info.get('streams', []):
        if stream.get('codec_type') == 'subtitle':
            # 获取字幕流的索引
            stream_index = stream['index']
            # 获取文件名字和扩展名
            base_name, _ = os.path.splitext(file_path)
            # 获取语言信息
            language = stream.get('tags', {}).get('language', 'unknown')
            # 如果不是中文则跳过
            if language not in ['zh', 'zho', 'chi', 'chs', 'cht', 'cn']:
                continue
            # 输出的字幕文件名：原文件名.字幕语言.ass
            output_file = f"{base_name}.{language}.ass"
            
            # 检查文件是否存在并删除它
            if os.path.exists(output_file):
                os.remove(output_file)
            
            if extract_subtitles(file_path, output_file, stream_index):
                logger.info(f'成功提取内嵌字幕 - {output_file}')
                break

def danmu_generator(file_path, width=1920, height=1080, fontface='Arial', fontsize=50, alpha=0.8, duration=6):
    # 使用弹弹play api 获取弹幕
    comment_id = get_comment_ID(file_path)
    if(comment_id == None):
        logger.info("未找到对应弹幕 - " + file_path)
        return None
    generate_danmu_ass(comment_id,file_path,width, height, fontface, fontsize, alpha, duration)
    # 尝试搜索原生字幕
    sub2 = find_subtitle_file(file_path)
    # 尝试获取内嵌字幕
    if sub2 == None:
        try_extract_sub(file_path)
    sub2 = find_subtitle_file(file_path)
    # 生成内嵌字幕加弹幕文件
    if sub2 != None:
        combine_sub_ass(os.path.splitext(file_path)[0] + '.danmu.ass', sub2)
    else:
        logger.error('未找到原生字幕，跳过合并 - ' + file_path)

