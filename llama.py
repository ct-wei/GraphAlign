import base64

import requests
import json

from sympy.physics.units.systems.si import base_dims


def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
# API的URL
url = 'http://localhost:11434/api/chat'
input_text = "please describe this pi"
image_path = "/home/zyserver/SSM/SSM/pic/1.png"

base64_image = image_to_base64(image_path)
# 要发送的数据
data = {
    "model": "llama3.2-vision",
    "messages": [
        {"role":"system","content": input_text},
        {"role": "user","content": " ", "images": [base64_image]}
    ],
    "stream": False
}



# 将字典转换为JSON格式的字符串
json_data = json.dumps(data)

# 发送POST请求
response = requests.post(url, data=json_data, headers={'Content-Type': 'application/json'})


# 打印响应内容
print(response.text)