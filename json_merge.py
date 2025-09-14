import subprocess
import os
import sys
import math
import json
from pydub import AudioSegment
import dashscope
from openai import OpenAI
import base64
from dashscope import MultiModalConversation

from qwen_audio import query


def read_json_file(file_path):
    """读取JSON文件返回Python对象"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

query = "以下是出自同一视频的知识库内容，前者是从视频中提取，后者是从音频中提取，在保留原格式不变的情况下，将两个知识库融合，输出相同格式的json文件，只要纯json格式的输出，不要有其他说明。"

def merge():
    video_path = "SSM/video/com/TXYL41.mp4"  # 替换为你的视频路径
    name = video_path.split('/')[3].split('.')[0]
    data_video = read_json_file(f'SSM/video/json/{name}.json')
    data_audio = read_json_file(f'SSM/video/json/{name}_audio.json')


    client = OpenAI(
        # 如果没有配置环境变量，请用百炼API Key替换：api_key="sk-xxx"
        api_key= "sk-89508ba4c53e4f358ef6cb38ec24d4bd",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    reasoning_content = ""  # 定义完整思考过程
    answer_content = ""  # 定义完整回复
    is_answering = False  # 判断是否结束思考过程并开始回复

    # 创建聊天完成请求
    completion = client.chat.completions.create(
        model="qwq-plus",  # 此处以 qwq-32b 为例，可按需更换模型名称
        messages=[
            {"role": "user", "content": f"{query}:{data_video}and{data_audio}"}
        ],
        # QwQ 模型仅支持流式输出方式调用
        stream=True,
        # 解除以下注释会在最后一个chunk返回Token使用量
        # stream_options={
        #     "include_usage": True
        # }
    )

    print("\n" + "=" * 20 + "思考过程" + "=" * 20 + "\n")

    for chunk in completion:
        # 如果chunk.choices为空，则打印usage
        if not chunk.choices:
            print("\nUsage:")
            print(chunk.usage)
        else:
            delta = chunk.choices[0].delta
            # 打印思考过程
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content != None:
                print(delta.reasoning_content, end='', flush=True)
                reasoning_content += delta.reasoning_content
            else:
                # 开始回复
                if delta.content != "" and is_answering is False:
                    print("\n" + "=" * 20 + "完整回复" + "=" * 20 + "\n")
                    is_answering = True
                # 打印回复过程
                print(delta.content, end='', flush=True)
                answer_content += delta.content

    # print("=" * 20 + "完整思考过程" + "=" * 20 + "\n")
    # print(reasoning_content)
    print("=" * 20 + "完整回复" + "=" * 20 + "\n")
    print(answer_content)
    json_str = answer_content[7:-3].strip()
    print(json_str)
    with open(f'SSM/video/json/{name}_all.json', 'w', encoding='utf-8') as f:
        json.dump(json.loads(json_str), f, ensure_ascii=False, indent=4)

merge()