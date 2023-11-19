import os

def delete_file_without_plot(file_path):
        with open(file_path, "r") as file:
            text = file.read()

            start_tag = "<plot>"
            end_tag = "</plot>"

            start_index = text.find(start_tag)
            end_index = text.find(end_tag)
            
            if start_index == -1 or end_index == -1:
                print(f'元数据没找到plot标签')
                return
            print(f'start_index: {start_index}, end_index: {end_index}')
            print(len(start_tag))
            print(end_index >= start_index + len(start_tag))
            if end_index >= start_index + len(start_tag):
                content = text[start_index + len(start_tag):end_index]
                if content.strip():
                    pass
                else:
                    print(f'plot标签为空，删除 {file_path}...')
                    # os.remove(file_path)
            else:
                print.info("元数据没找到plot标签，跳过...")

delete_file_without_plot("/Volumes/Garage/Anime/米奇与达利 (2023)/Season 1/米奇与达利 - S01E04.nfo")