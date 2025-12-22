import os
import json
import re
import logging
import base64  # 新增：用于图片Base64编码
from pathlib import Path
# from dashscope import MultiModalConversation # 删除或注释掉旧的导入
# import dashscope # 删除或注释掉旧的导入
import openai  # 新增：OpenAI SDK
import traceback # 确保已导入 traceback

# --- 配置区域 ---
OPENAI_API_KEY = 'sk-2368088ca7ff4256bf082eb55d3df622' # 直接设置 API Key
# OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') # 推荐：通过环境变量设置 API Key
MODLE_TYPE = 'qwen3-vl-flash'
'''
        qwen3 - vl - plus：性能最强的模型。
        qwen3 - vl - flash：速度更快，成本更低，是兼顾性能与成本的高性价比选择，适用于对响应速度敏感的场景。
        对于简单的图像描述、短视频摘要提取等通用任务，可选        Qwen2.5 - VL，系列内模型对比如下：
        qwen - vl - plus：速度更快，在效果与成本之间实现良好平衡。
'''
if not OPENAI_API_KEY:
    raise ValueError("请设置环境变量 OPENAI_API_KEY")

OPENAI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1" # 默认 OpenAI 地址，可改为其他兼容平台地址
# OPENAI_BASE_URL = "https://your-proxy-or-local-server/v1/" # 示例：使用代理或本地部署

IMAGE_FOLDER_PATH = './book_covers/normal'
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.gif'} # 确保支持的格式符合模型要求
OUTPUT_FORMAT = 'json'  # 'json' 或 'txt'

# 重试配置
MAX_RETRIES = 1  # 最多重试1次（总共尝试2次）

# 日志和提示词文件配置
LOG_FILE_NAME = "processing_errors.log"
PROMPT_FILE_NAME = "./config/prompt.txt"  # 指定提示词文件名

# --- 初始化 OpenAI 客户端 ---
client = openai.OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

# --- 设置日志记录器 ---
logging.basicConfig(
    filename=LOG_FILE_NAME,
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

# --- 从文件读取 Prompt ---
def load_prompt(prompt_file_path):
    """从指定的文本文件加载Prompt"""
    prompt_path = Path(prompt_file_path)
    if not prompt_path.exists():
        print(f"错误：找不到提示词文件 '{prompt_file_path}'。请确认文件存在。")
        exit(1)

    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_text = f.read()
        print(f"成功从 '{prompt_file_path}' 加载提示词。")
        return prompt_text.strip()
    except Exception as e:
        print(f"读取提示词文件 '{prompt_file_path}' 时出错: {e}")
        exit(1)

# 在初始化阶段加载Prompt
PROMPT_TEXT = load_prompt(PROMPT_FILE_NAME)

def is_image_file(file_path):
    """检查文件是否为支持的图片格式"""
    return file_path.suffix.lower() in SUPPORTED_EXTENSIONS

# --- 新增：将图片文件转为 Base64 Data URL ---
def encode_image_to_base64(image_path):
    """将图片文件编码为 base64 字符串，用于 OpenAI API"""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        # 确定 MIME 类型 (可以根据扩展名简单推断)
        mime_type = "image/jpeg" # 默认
        ext = image_path.suffix.lower()
        if ext == '.png':
            mime_type = "image/png"
        elif ext in ['.bmp']:
            mime_type = "image/bmp"
        elif ext in ['.webp']:
            mime_type = "image/webp"
        elif ext in ['.gif']:
             mime_type = "image/gif"

        data_url = f"data:{mime_type};base64,{encoded_string}"
        return data_url
    except Exception as e:
        raise ValueError(f"编码图片 '{image_path}' 时出错: {e}")

def extract_json_from_response(response_content):
    """从模型的回复内容中尝试提取JSON字符串。"""
    full_text = ""
    # OpenAI 的 response_content 通常是字符串
    if isinstance(response_content, str):
        full_text = response_content
    else:
        full_text = str(response_content)

    start_idx = full_text.find('{')
    end_idx = full_text.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        potential_json = full_text[start_idx:end_idx + 1]
        if potential_json.count('{') == potential_json.count('}'):
            return potential_json
    return None

def log_error(image_path, error_message, raw_output=""):
    """统一记录错误日志"""
    log_msg = f"图片 '{image_path.name}': {error_message}"
    if raw_output:
        truncated_output = (raw_output[:500] + '...') if len(raw_output) > 500 else raw_output
        log_msg += f" | 原始输出 (截断): {truncated_output}"
    logger.error(log_msg)
    print(log_msg)

# --- 修改：封装 OpenAI API 调用逻辑 ---
def call_openai_api(base64_image_data_url):
    """封装 OpenAI API 调用逻辑"""
    try:
        # --- 修改模型名称 ---
        # 请根据你的需求和可用性选择模型
        # gpt-4-turbo, gpt-4o, 或其他支持视觉输入的模型
        selected_model = MODLE_TYPE # <--- 修改为你想用的模型
        print(f"    调用模型: {selected_model}")

        response = client.chat.completions.create(
            model=selected_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT_TEXT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": base64_image_data_url,
                                # "detail": "low" # 可选：调整图片细节级别以节省 tokens ("low", "high", "auto")
                            },
                        },
                    ],
                }
            ],
            # max_tokens=300, # 可选：限制最大输出 token 数
        )
        return response
    except Exception as e:
        error_details = f"OpenAI API 调用抛出异常: {type(e).__name__}: {e}"
        tb_str = traceback.format_exc()
        detailed_error = f"{error_details}\n堆栈跟踪:\n{tb_str}"
        print(f"    [ERROR] {error_details}")
        return {
            "status_code": -1,
            "error": detailed_error,
            "original_exception": str(e)
        }

def analyze_book_cover(image_path):
    """
    调用 OpenAI 视觉模型分析单张书籍封面图片，带重试机制。
    """
    try:
        # --- 关键步骤：将图片编码为 Base64 Data URL ---
        base64_image = encode_image_to_base64(image_path)
        print(f"  -> 图片已编码为 Base64 Data URL")
    except Exception as e:
        error_msg = f"图片编码失败: {e}"
        log_error(image_path, error_msg)
        return {"success": False, "error": error_msg, "raw_output": "N/A"}

    for attempt in range(MAX_RETRIES + 1):
        try:
            print(f"  -> 发送API请求 (第 {attempt + 1} 次尝试)")
            response = call_openai_api(base64_image)

            # 检查是否是我们自定义的错误字典
            if isinstance(response, dict) and response.get("status_code") == -1:
                 error_msg = f"API调用失败 (尝试 {attempt + 1})"
                 log_error(image_path, error_msg, response.get('error', 'No detailed error'))
                 if attempt < MAX_RETRIES:
                     continue
                 else:
                      # 返回原始异常信息
                      return {"success": False, "error": response.get('original_exception', 'Unknown Error during API call'), "raw_output": response.get('error', 'No detailed error')}

            # 检查是否是成功的 OpenAI 响应对象
            if hasattr(response, 'choices') and len(response.choices) > 0:
                # 成功获取响应
                model_reply_content = response.choices[0].message.content # 获取模型的文本回复

                json_str = extract_json_from_response(model_reply_content)

                if json_str:
                    try:
                        result_data = json.loads(json_str)
                        print(f"    成功解析结果 (第 {attempt + 1} 次尝试)")
                        return {"success": True, "data": result_data}
                    except json.JSONDecodeError as je:
                        error_msg = f"JSON解析失败 (尝试 {attempt + 1}): {je}"
                        log_error(image_path, error_msg, str(model_reply_content))
                        if attempt < MAX_RETRIES:
                            continue
                        else:
                            return {"success": False, "error": error_msg, "raw_output": model_reply_content}
                else:
                    error_msg = f"无法在模型回复中找到JSON结构 (尝试 {attempt + 1})"
                    log_error(image_path, error_msg, str(model_reply_content))
                    if attempt < MAX_RETRIES:
                        continue
                    else:
                        return {"success": False, "error": error_msg, "raw_output": model_reply_content}

            else:
                # API 返回了非预期的成功响应格式
                error_msg = f"API返回了非预期的响应格式 (尝试 {attempt + 1})"
                log_error(image_path, error_msg, str(response))
                if attempt < MAX_RETRIES:
                    continue
                else:
                    return {"success": False, "error": error_msg, "raw_output": str(response)}

        except Exception as e:
            error_msg = f"处理图片 '{image_path.name}' 时发生未知错误 (尝试 {attempt + 1}): {e}"
            tb_str = traceback.format_exc()
            log_error(image_path, error_msg, tb_str)
            if attempt < MAX_RETRIES:
                continue
            else:
                return {"success": False, "error": error_msg, "raw_output": tb_str}

    final_error = f"经过 {MAX_RETRIES + 1} 次尝试后仍然失败。"
    log_error(image_path, final_error)
    return {"success": False, "error": final_error, "raw_output": "N/A"}

# --- save_result 和 main 函数保持不变 ---
# ... (这部分代码不需要修改，除了可能的日志消息前缀可以改一下) ...

def save_result(image_path, result):
    """将分析结果保存到文件。"""
    base_name = image_path.stem
    output_dir = image_path.parent

    if OUTPUT_FORMAT.lower() == 'json':
        output_file_path = output_dir / f"{base_name}.json"
        try:
            with open(output_file_path, 'w', encoding='utf-8') as f:
                if result["success"]:
                    json.dump(result["data"], f, indent=4, ensure_ascii=False)
                else:
                    error_info = {
                        "error": result["error"],
                        "raw_model_output": result.get("raw_output", "N/A")
                    }
                    json.dump(error_info, f, indent=4, ensure_ascii=False)
            print(f"    结果已保存至: {output_file_path}")
        except Exception as e:
            error_msg = f"保存文件 '{output_file_path}' 时出错: {e}"
            log_error(image_path, error_msg)

    elif OUTPUT_FORMAT.lower() == 'txt':
        output_file_path = output_dir / f"{base_name}.txt"
        try:
            with open(output_file_path, 'w', encoding='utf-8') as f:
                if result["success"]:
                    data = result["data"]
                    f.write(f"译者: {data.get('Translator', 'N/A')}\n")
                    f.write(f"编者名: {data.get('Editor', 'N/A')}\n")
                    f.write(f"主书名: {data.get('Main_Title', 'N/A')}\n")
                    f.write(f"副标题: {data.get('Subtitle', 'N/A')}\n")
                    f.write(f"出版社: {data.get('Publishing_House', 'N/A')}\n")
                    f.write(f"腰封: {data.get('Book_Jacket', 'N/A')}\n")
                    f.write(f"内容简介/推荐语: {data.get('Content_Introduction_Recommendation', 'N/A')}\n")
                    f.write("\n--- 封面的描述 ---\n")
                    f.write(data.get('Description_of_the_Cover', 'N/A'))
                else:
                    f.write(f"处理失败: {result['error']}\n")
                    if "raw_output" in result:
                        f.write(f"\n原始模型输出:\n{result['raw_output']}\n")
            print(f"    结果已保存至: {output_file_path}")
        except Exception as e:
            error_msg = f"保存文件 '{output_file_path}' 时出错: {e}"
            log_error(image_path, error_msg)
    else:
        print(f"不支持的输出格式: {OUTPUT_FORMAT}")

def main():
    """主函数，遍历文件夹并处理图片"""
    folder_path = Path(IMAGE_FOLDER_PATH)

    if not folder_path.exists() or not folder_path.is_dir():
        print(f"错误：指定的路径 '{IMAGE_FOLDER_PATH}' 不存在或不是一个目录。")
        return

    print(f"开始处理文件夹 (使用 OpenAI API): {folder_path.resolve()}")
    print(f"错误日志将记录在: {LOG_FILE_NAME}")
    print(f"使用的提示词来自: {PROMPT_FILE_NAME}")

    processed_count = 0
    success_count = 0

    for item in folder_path.iterdir():
        if item.is_file() and is_image_file(item):
            processed_count += 1
            print(f"\n[{processed_count}] 正在处理图片: {item.name}")
            result = analyze_book_cover(item)
            if result["success"]:
                success_count += 1
            save_result(item, result)

    print(f"\n处理完成。总计处理 {processed_count} 张图片，成功 {success_count} 张。")

if __name__ == "__main__":
    main()