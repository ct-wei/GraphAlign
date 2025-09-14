import json
import os
from openai import OpenAI
import base64


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def process_images_in_folder(folder_path):
    # 获取文件夹中所有图片文件
    image_files = [f for f in os.listdir(folder_path)
                   if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]

    # 按文件名排序
    image_files.sort()

    base64_images = []
    for image_file in image_files:
        image_path = os.path.join(folder_path, image_file)
        base64_images.append(f"data:image/png;base64,{encode_image(image_path)}")

    return base64_images


# 指定包含图片的文件夹路径
image_folder = "SSM/video/output"  # 替换为你的文件夹路径
base64_video_frames = process_images_in_folder(image_folder)

if not base64_video_frames:
    print("文件夹中没有找到图片文件！")
    exit()

client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key="sk-89508ba4c53e4f358ef6cb38ec24d4bd",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

input_text = """观看视频，深度理解视频，进行详细知识整理，建立层级化的课程知识库，输出json格式的文本，只要纯json格式的输出，不要有其他说明, 下面是一个例子：
{
    "通信原理": {
        "第4章 信道与噪声": {
            "第5讲 信道容量": {
                "4.5.1 无扰信道的容量——奈奎斯特定理": {
                    "公式": "C = 2B log_2 M (b/s)",
                    "参数说明": {
                        "B": "信道带宽（Hz）",
                        "M": "信号电平数（进制数）"
                    },
                    "实例分析": {
                        "带宽": "3000 Hz",
                        "信号电平数": [
                            {"M=2": "C=6000 b/s"},
                            {"M=4": "C=12000 b/s"},
                            {"M=8": "C=18000 b/s"}
                        ],
                        "思考问题": "能否无限增大信号电平数M或信道带宽B来提高信道容量C？"
                    }
                },
                "4.5.2 有扰信道的容量——香农公式": {
                    "公式": "C = B log_2 (1 + S/N) (b/s)",
                    "参数说明": {
                        "S": "信号平均功率（W）",
                        "N": "噪声功率（W）",
                        "n_0": "噪声单边功率谱密度（W/Hz）",
                        "B": "信道带宽（Hz）"
                    },
                    "结论": [
                        "信道容量C依赖于B、S和n_0三要素。",
                        "B一定，增大S或减小n_0（即提高S/N），可增大C。",
                        "S/n_0一定，当B→∞时，C趋于有限值：lim_{B→∞} C ≈ 1.44(S/n_0)"
                    ],
                    "应用": [
                        "增加B，可以换取S/N的降低——适用于宇宙飞行、深空探测、CDMA等场景。",
                        "提高S/N，可以换取B的减小——适用于有线载波电话、频带拥挤场合。"
                    ],
                    "意义": [
                        "证明了理想通信系统的‘存在性’；",
                        "虽未给出具体实现方法，但仍具有重要的指导意义；",
                        "提供了一个衡量实际通信系统性能的标准；",
                        "为后人指出了努力的方向或目标。"
                    ]
                },
                "例题": {
                    "题目": "有一个1MHz带宽的信道，其信噪比为63，求合适的信息速率R_b和信号电平数M。",
                    "解题步骤": [
                        "使用香农公式确定信道容量：C = B log_2 (1 + S/N) = 10^6 × log_2 (1 + 63) = 6 (Mb/s)",
                        "按照奈奎斯特定理确定信号电平数：C = 2B log_2 M → M = 8"
                    ]
                }
            }
        },
        "配套教材": [
            "《通信原理（第7版）》, 樊昌信、曹丽娜编, 国防工业出版社",
            "《现代通信原理与技术（第4版）》, 张辉, 西安电子科技大学出版社",
            "《通信原理（第7版）学习辅导与考研指导/》, 曹丽娜、陈英"
        ]
    }
}
"""

completion = client.chat.completions.create(
    model="qwen-vl-max",
    messages=[
        {"role": "system",
         "content": [{"type": "text", "text": "You are a helpful assistant."}]},
        {"role": "user", "content": [
            {"type": "video", "video": base64_video_frames},
            {"type": "text", "text": input_text},
        ]}]
)
response_content = completion.choices[0].message.content
json_str = response_content[7:-3].strip()
print(json_str)
name = "TXYL45"
with open(f'SSM/video/json/{name}.json', 'w', encoding='utf-8') as f:
    json.dump(json.loads(json_str), f, ensure_ascii=False, indent=4)



