import requests
import json
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from collections import namedtuple,defaultdict
from dataclasses import dataclass, asdict
import math


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

url = "https://tlidb.com/cn/Talent"
response = requests.get(url, headers=headers)
Talent_Name_Map = {}
if response.status_code == 200:
  soup = BeautifulSoup(response.text, 'html.parser')
  target = soup.find('div', {'id':"Profession", 'class':'tab-pane fade show active'}).find('div', {'class':'row row-cols-1 row-cols-lg-3 g-2'})
  for i in target:
    for j in i.find('div').find_all('div')[1::2]:
        a_tag = j.find('a')  # 提取<a>标签内容
        text_content = a_tag.text if a_tag else "无"
        href_value = a_tag['href'] if a_tag else "无"
    if('New_God' in href_value):
        continue
    Talent_Name_Map[text_content] = href_value




@dataclass
class SmallTalent:
    title: str
    descriptions: str
    x: int
    y: int
    id: int
    dependce: int = None
    at_least: int = None
    level_up_time: int = None
    img_url: str = None

def get_talent(url, name, value): 

    response = requests.get(talent_url, headers=headers)
    if response.status_code == 200:
        # 使用BeautifulSoup解析HTML
        # print(response.text)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        svg = soup.find('svg')

        lines = svg.find('g', class_='connections').find_all('line')

        # 解析依赖关系
        dependencies_line = []
        for line in lines:
            x1 = int(line['x1'])
            y1 = int(line['y1'])
            x2 = int(line['x2'])
            y2 = int(line['y2'])
            dependencies_line.append({'start': ((x2, y2)), 'end': (x1, y1)})

        def calculate_distance_2d(x1, y1, x2, y2):
            return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

        def merge_start_coordinates(data):
            merged_data = defaultdict(list)
            
            # 遍历所有字典，将相同 start 坐标的 end 合并到一起
            for item in data:
                start = item['start']
                end = item['end']
                merged_data[start].append(end)
            
            # 将合并后的数据转换成字典列表格式
            result = [{'start': start, 'end': ends} for start, ends in merged_data.items()]
            return result
        
        dependencies_line = merge_start_coordinates(dependencies_line)

        
        ## 提取天赋的限制点数
        points = svg.find_all('text', class_='points')
        at_leasts = []
        # 提取每个元素的 x, y 属性和文本内容
        zero_point = (int(points[0].get('x')), int(points[0].get('y')))
        for element in points:
            x = int(element.get('x'))
            at_least = int(element.get_text())  # 提取文本内容
            at_leasts.append((x, at_least))

        # 提取天赋文本
        # 提取所有的 <circle>, <image>, <text> 元素
        g_elements = svg.find('g', class_='nodes')

        # 遍历所有找到的 <g> 元素并提取信息
        # print(g_elements)
        # 查找 <circle> 元素
        circles_soup = g_elements.find_all('circle', class_='talent_bg')
        # 查找 <text> 元素
        texts_soup = g_elements.find_all('text', class_="level_up_time")
        # 查找 <image> 元素
        images_soup = g_elements.find_all('image', class_="talent")
        
        
        assert(len(circles_soup) == len(texts_soup))
        assert(len(circles_soup) ==len(images_soup))
        circles=[]
        for circle in circles_soup:
            if circle is not None:
                cx = int(circle.get('cx', None))
                cy = int(circle.get('cy', None))
                r = int(circle.get('r', None))
            circles.append((cx, cy, r))
        
        level_up_times = []
        for text in texts_soup:
            if text is not None:
                x = text.get('x', None)
                y = text.get('y', None)
                content = int(text.text.strip() if text.text else None)
                level_up_times.append(content)
        
        combined_array = [tuple for tuple in zip(circles, level_up_times, images_soup)]
        # print(combined_array)
        # 提取每个天赋的 src, data-bs-title, x, y 属性
        id = 0
        talent_map = {}
        for circle, level_up_time, img in combined_array:
            title = img.get('data-bs-title', None)  # 获取 data-bs-title 属性
            x = circle[0]  # 获取 x 属性
            y = circle[1]  # 获取 y 属性
            img_url = img.get('xlink:href', None)  # 获取 data-bs-title 属性
            
            if title:
                # 使用 BeautifulSoup 解析 data-bs-title 的 HTML 内容
                tooltip_soup = BeautifulSoup(title, 'html.parser')
                strong_tag = tooltip_soup.find('strong')  # 提取 <strong> 内容
                title = strong_tag.text if strong_tag else None
                descriptions = [line.strip() for line in tooltip_soup.stripped_strings if line != title]
            else:
                title = None
                descriptions = []
            # 输出结果
            talent_map[id] = SmallTalent(title=title, descriptions=descriptions, level_up_time=level_up_time, x=x, y=y, id=id, img_url=img_url, dependce=None, at_least=None)
            id = id + 1

        for id,talent in talent_map.items():
            for line in dependencies_line:
                if(len(line['start']) == 2 and calculate_distance_2d(talent.x, talent.y, line['start'][0], line['start'][1]) < 40):
                    line['start'] = [id]
        
        for id,talent in talent_map.items():
            for line in dependencies_line:
                updated_ends = []
                for end in line['end']:
                    if(len(end) == 2 and calculate_distance_2d(talent.x, talent.y, end[0], end[1]) < 40):
                        updated_ends.append([id])
                    else:
                        updated_ends.append(end)
                line['end'] = updated_ends
        
        for line in dependencies_line:
            assert(len(line['start']) == 1)
            for i in line['end']:
               assert(len(i) == 1)
               talent_map[i[0]].dependce = line['start'][0]
        
        for id,talent in talent_map.items():
            assert talent.at_least == None
            for i in at_leasts:
                if(abs(i[0] - talent.x) < 32):
                    talent.at_least = i[1]
            assert talent.at_least != None
            assert(talent_map[id].x >=zero_point[0])
            assert(talent_map[id].y >=zero_point[1])
            talent_map[id].x = talent.x - zero_point[0]
            talent_map[id].y = talent.y - zero_point[1]
        return talent_map 
        
    else:
        print("Failed to fetch the page:", response.status_code)


@dataclass
class CoreTalent:
    title: str
    id: int
    descriptions: str
    points: int
    img_url: str

def get_core_talent(url, name, value):
    response = requests.get(talent_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
        
    targrts = soup.find_all('div', {'class': 'col'})
    id = 0
    core_talents_map = {}
    for col in targrts[0:6]:
        img_url = col.find('img').get('src', None)
        # 提取<strong>标签的文本
        strong_tag = col.find('strong')
        # 获取文本内容
        name = strong_tag.text if strong_tag else None
        
        # 提取点数需求
        points_tag = col.find_all('span')[0]  # 第一个 span 是点数需求
        points = points_tag.text if points_tag else None
        
        # 提取解锁状态
        unlock_status_tag = col.find_all('span')[1]  # 第二个 span 是解锁状态
        unlock_status = unlock_status_tag.text if unlock_status_tag else None
        
        # 提取效果描述
        effect_description = col.find_all(string=True)
        effect = ' '.join(effect_description).strip()  # 提取所有文本并合并
        effect = effect.split('0/1')[-1]
        points = int(points.strip('pts'))
        core_talent = CoreTalent(title=name, points=points, descriptions=effect, id=id, img_url=img_url)
        core_talents_map[id] = core_talent
        id = id + 1
    return core_talents_map
        
        
    

@dataclass
class Talent:
    name: str
    core_talents_map: dict 
    small_talents_map: dict


talent_list = list(Talent_Name_Map.keys())

talent_group = []
for i, val in enumerate(talent_list[0:6]):
    start_index = i * 3
    no_base_talent = talent_list[6:][start_index:start_index + 3]
    if len(no_base_talent) == 3:  
        no_base_talent.insert(0, val)
        talent_group.append(no_base_talent)


result = []
for i in talent_group:
    assert[len(i) == 4]
    talent_name_group = ((i[0], Talent_Name_Map[i[0]]),
     (i[1], Talent_Name_Map[i[1]]),
     (i[2], Talent_Name_Map[i[2]]),
     (i[3], Talent_Name_Map[i[3]]))
    result.append(talent_name_group)

file_path = "out/patent_list.txt"
with open(file_path, 'w', encoding='utf-8') as file:
    json.dump(result, file, ensure_ascii=False, indent=4)


for name, value in Talent_Name_Map.items():
    talent_url = "https://tlidb.com/cn/" + value + "#Talent"
    core_talent_url = "https://tlidb.com/cn/" + value + "#"+ name
    small_talents_map = get_talent(talent_url, name, value)
    core_talents_map = get_core_talent(core_talent_url, name, value)
    talent = Talent(name=name, core_talents_map=core_talents_map, small_talents_map=small_talents_map)
    talent_dict = asdict(talent)
    talent_json = json.dumps(talent_dict, indent=4, ensure_ascii=False)
    file_path = "out/patent_"+value+".txt"
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(talent_dict, file, ensure_ascii=False, indent=4)
