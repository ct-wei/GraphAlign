import base64
import requests
import json
import re
import time
import torch
from torch.cuda import graph

print(torch.cuda.is_available())
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
import json

# 初始空的 JSON 数据结构


# 定义添加主题的函数
def add_scene(data, description):
    data["scene"] = description
    return data

# 定义添加区域的函数
def add_region(data, region_name, description):
    new_region = {
        "region_name": region_name,
        "description": description,
        "objects": []
    }
    data["regions"].append(new_region)
    return data

# 定义添加对象的函数
def add_object(data, region_name, name, attributes):
    # 在指定的区域内添加对象
    for region in data["regions"]:
        if region["region_name"] == region_name:
            new_object = {
                "name": name,
                "attribute": attributes
            }
            region["objects"].append(new_object)
            break
    return data

# 定义添加关系的函数
def add_triple(data, subject, relationship, object_):
    new_triple = {
        "subject": subject,
        "relationship": relationship,
        "object": object_
    }
    data["triples"].append(new_triple)
    return data

# 保存 JSON 文件的函数
def save_to_file(data, file_name="output.json"):
    with open(file_name, "w") as file:
        json.dump(data, file, indent=4)
    print(f"Data saved to {file_name}")

def theme_get(url, base64_image):
    question = (
        "Describe the theme of the image in a brief sentence, and give me only one sentence as the answer, for example: an inspiring basketball game.")
    # Getting the base64 string

    data = {
        "model": "llama3.2-vision",
        "messages": [
            {"role": "system", "content": question},
            {"role": "user", "content": " ", "images": [base64_image]}
        ],
        "stream": False
    }
    # 将字典转换为JSON格式的字符串
    json_data = json.dumps(data)
    # 发送POST请求
    response = requests.post(url, data=json_data, headers={'Content-Type': 'application/json'})
    theme = response.json()['message']['content']
    return theme

def region_get(url, base64_image, theme):
    question = (
        f"""
            Please divide the image into two regions based on events surrounding this theme({theme}) ,with each event as one region and all background as one region.
            Only output the name of each region, without any additional content, provide the answer in the following format:
            **A group of men playing basketball**
            **Spectators watching the basketball game**
            **Basketball court**
        """)
    # Getting the base64 string

    data = {
        "model": "llama3.2-vision",
        "messages": [
            {"role": "system", "content": question},
            {"role": "user", "content": " ", "images": [base64_image]}
        ],
        "stream": False
    }
    # 将字典转换为JSON格式的字符串
    json_data = json.dumps(data)
    # 发送POST请求
    response = requests.post(url, data=json_data, headers={'Content-Type': 'application/json'})
    regions = response.json()['message']['content']
    return regions

def extact_region(regions):
    words = re.findall(r"\*\*(.*?)\*\*", regions)
    return words

def extract_object(objects):
    # 正则表达式：提取区域和每个区域的对象及其属性
    pattern = r"\*\*(.*?)\*\*\n((?:\*.*?:\s*\[.*?\]\n?)*)"

    # 查找所有匹配项
    matches = re.findall(pattern, objects)

    # 输出结构化的数据
    data = {}

    for region, objects in matches:
        region = region.strip()  # 去除区域名称两端的空格
        data[region] = []

        # 提取每个区域中的对象及其属性
        object_pattern = r"\* (.*?): \s*\[(.*?)\]"
        object_matches = re.findall(object_pattern, objects)

        for obj, attributes in object_matches:
            attributes_list = [attr.strip() for attr in attributes.split(',')]  # 按逗号分割属性并去除空格
            data[region].append({
                'object': obj.strip(),
                'attributes': attributes_list
            })

    return data

def object_get(url, base64_image, regions):
    question = (
        f"""
            Please extract the objects related to each region and their attributes according to the region descriptions({regions}). 
            Only output objects and attributes, without any additional content.
            with regions enclosed in ** (e.g., **region1**), and objects preceded by * (e.g., * object1).
            Strictly follow the format below for output:
            **region1**
            *object1: [attr1, attr2, attr3].
            *object2: [attr1, attr2, attr3].
            
            **region2**
            *object3: [attr1, attr2, attr3].
            *object4: [attr1, attr2, attr3].
        """)
    # Getting the base64 string

    data = {
        "model": "llama3.2-vision",
        "messages": [
            {"role": "system", "content": question},
            {"role": "user", "content": " ", "images": [base64_image]}
        ],
        "stream": False
    }
    # 将字典转换为JSON格式的字符串
    json_data = json.dumps(data)
    # 发送POST请求
    response = requests.post(url, data=json_data, headers={'Content-Type': 'application/json'})
    regions = response.json()['message']['content']
    return regions

def understand(image_path, image_name):
    # OpenAI API Key
    graph_data = {
        "scene": "",
        "regions": [],
        "triples": []
    }
    url = 'http://localhost:11434/api/chat'    # Path to your image
    base64_image = encode_image(image_path)
    theme = theme_get(url, base64_image)
    graph_data = add_scene(graph_data, theme)
    print(graph_data)

    regions = region_get(url, base64_image, theme)
    regions = extact_region(regions)
    print(regions)
    for i in range(len(regions)):
        graph_data = add_region(graph_data, f"region{i+1}", regions[i])

    objects = object_get(url, base64_image, regions)
    objects = extract_object(objects)
    print(objects)
    for region, items in objects.items():
        print(region)
        for item in items:
            graph_data = add_object(graph_data, region, item['object'], item['attributes'])

    print(graph_data)


    return graph_data


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')






# Example usage
def p2sgg(image_path):
    image_name = image_path.split('pic/')[1].split('.')[0]
    return understand(image_path, image_name)

p2sgg("/home/zyserver/SSM/SSM/pic/1.png")
