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

def extract_audio_ffmpeg(input_video, output_audio, format='mp3'):
    """
    使用 FFmpeg 提取视频音频

    参数:
        input_video (str): 输入视频文件路径
        output_audio (str): 输出音频文件路径（可选）
        format (str): 音频格式（mp3/wav等），默认mp3

    返回:
        str: 成功返回输出路径，失败返回None
    """
    try:
        # 自动生成输出路径
        if not output_audio:
            base_name = os.path.splitext(input_video)[0]
            output_audio = f"{base_name}_audio.{format}"

        # 创建输出目录（如果不存在）
        os.makedirs(os.path.dirname(output_audio), exist_ok=True)

        # FFmpeg 命令参数
        cmd = [
            'ffmpeg',
            '-y',  # 覆盖已存在文件
            '-i', input_video,
            '-vn',  # 禁用视频流
            '-acodec', 'libmp3lame' if format == 'mp3' else 'pcm_s16le',  # 编码器
            '-q:a', '0' if format == 'mp3' else None,  # 最高音质（MP3）
            '-ar', '11025',  # 采样率
            # '-ac', '2',  # 声道数
            output_audio
        ]
        cmd = [arg for arg in cmd if arg is not None]  # 清理空参数

        # 执行命令
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        # 错误处理
        if result.returncode != 0:
            error_msg = f"FFmpeg 错误:\n{result.stderr}"
            raise RuntimeError(error_msg)

        print(f"✅ 音频已提取到: {output_audio}")
        return output_audio

    except Exception as e:
        print(f"❌ 提取失败: {str(e)}")
        return None
def audio_to_base64(audio_path):
    """将音频文件转换为Base64编码"""
    with open(audio_path, "rb") as audio_file:
        return base64.b64encode(audio_file.read()).decode("utf-8")




def calculate_chunk_duration(audio_path, max_size_mb=10):
    """根据文件大小计算分块时长"""
    # Base64编码会增加约33%的体积
    file_size = os.path.getsize(audio_path)  # 字节
    max_raw_size = max_size_mb * 1024 * 1024 / 1.37  # 换算原始文件最大尺寸

    audio = AudioSegment.from_file(audio_path)
    bitrate = audio.frame_rate * audio.frame_width * 8  # 计算比特率 (bps)

    # 计算最大允许时长（秒）
    max_duration = (max_raw_size * 8) / bitrate  # 秒
    return math.floor(max_duration)


def split_audio(input_path, chunk_duration):
    """分割音频文件"""
    audio = AudioSegment.from_file(input_path)
    chunks = []

    for i in range(0, len(audio), chunk_duration * 1000):
        chunk = audio[i:i + chunk_duration * 1000]
        chunk_path = f"temp_chunk_{len(chunks)}.mp3"
        chunk.export(chunk_path, format="mp3")
        chunks.append(chunk_path)

    return chunks


def process_audio_chunks(output_audio_path):
    """处理音频分块的主函数"""

    dashscope.api_key = "sk-89508ba4c53e4f358ef6cb38ec24d4bd"

    # 1. 计算合适的分块时长
    chunk_duration = calculate_chunk_duration(output_audio_path)
    print(f"自动计算分块时长：{chunk_duration}秒/块")

    # 2. 分割音频
    chunk_files = split_audio(output_audio_path, chunk_duration)

    # 3. 分块处理
    full_transcript = []
    for i, chunk_path in enumerate(chunk_files):
        print(f"正在处理第 {i + 1}/{len(chunk_files)} 块...")

        try:
            # 转换为Base64
            audio_base64 = audio_to_base64(chunk_path)

            # 构建消息
            messages = [
                {
                    "role": "system",
                    "content": [{"text": "You are a helpful assistant."}]},
                {
                    "role": "user",
                    "content": [{"audio": chunk_path}, {"text": "音频里在说什么?,整理一下，给出详细的内容"}],
                }
            ]



            # 调用API
            response = MultiModalConversation.call(
                model="qwen-audio-turbo-latest",
                messages=messages
            )

            # 提取结果
            if response.status_code == 200:
                response_content = response.output.choices[0].message.content[0]['text']
                full_transcript.append(response_content)
            else:
                print(f"第 {i + 1} 块处理失败：{response.message}")

        finally:
            # 清理临时文件
            os.remove(chunk_path)

    # 4. 整合结果
    return "\n".join(full_transcript)

query = """将下列内容详细整理，形成层级化的知识库，以json格式的文件输出, 只要纯json格式的输出，不要有其他说明, 下面是一个例子：
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

if __name__== "__main__":    # 使用示例
    video_path = "SSM/video/com/TXYL41.mp4"  # 替换为你的视频路径
    name = video_path.split('/')[3].split('.')[0]
    output_audio_path = f"SSM/video/mp3/{name}.mp3"
    # 提取为MP3（默认）
    audio_mp3 = extract_audio_ffmpeg(video_path, output_audio_path)

    # # 提取为WAV
    # audio_wav = extract_audio_ffmpeg(
    #     video_path,
    #     output_audio="SSM/video/mp3/audio.wav",
    #     format='wav'
    # )


    # 示例：提取音频并转换为Base64
    final_result = process_audio_chunks(output_audio_path)
    print(final_result)
    print("LMM dealing...")
    # 初始化OpenAI客户端
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
            {"role": "user", "content": f"{query}:{final_result}"}
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
    with open(f'SSM/video/json/{name}_audio.json', 'w', encoding='utf-8') as f:
        json.dump(json.loads(json_str), f, ensure_ascii=False, indent=4)

