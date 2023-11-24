import os
import re
def update_nfo(file_path: str):
    # 获取评分
    rank = 1
    if rank == None: return False

    # 更新NFO
    if not os.path.exists(file_path):
        print(f"{file_path} 不存在")
        return False
    print(f'准备处理 {file_path}...')
    with open(file_path, 'r') as file:
        content = file.read()
    content = re.sub(r'<rating>.*?</rating>', f'<rating>{rank}</rating>', content)
    if re.search(r'<rating>.*?</rating>', content) == None:
        print(f"{file_path} 中没有rating字段")
        return False
    with open(file_path, 'w') as file:
        file.write(content)
        print(f"更新{file_path}的评分为{rank}")
        return True
    
update_nfo('/Volumes/Garage/Movies/机动警察 和平保卫战 (1993)/机动警察 和平保卫战 (1993).nfo')