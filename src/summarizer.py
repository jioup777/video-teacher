#!/usr/bin/env python3
"""
笔记生成模块 - 使用 GLM-4-Flash 生成结构化学习笔记
"""

import requests
import sys
from typing import Optional, Dict


def generate_note(
    transcript: str,
    glm_config: Dict,
    verbose: bool = False
) -> Optional[str]:
    """
    使用 GLM-4-Flash 生成结构化学习笔记
    
    Args:
        transcript: 转录文本
        glm_config: GLM 配置（包含 api_key 和 model）
        verbose: 是否显示详细输出
    
    Returns:
        生成的笔记内容，失败返回 None
    """
    
    api_key = glm_config.get("api_key")
    model = glm_config.get("model", "glm-4-Flash")
    
    if not api_key:
        print("❌ 未提供 GLM API Key")
        return None
    
    # 构建提示词
    prompt = f"""你是一位专业的学习笔记整理专家。以下是视频的语音转录文本（有一些识别错误），请整理成结构化的学习笔记。

**转录文本**：
{transcript[:8000]}  # 限制长度，避免超出 token 限制

**注意**：文本中有一些语音识别错误，请根据上下文纠正。

**输出要求**：
1. **核心主题**：视频的主要内容是什么
2. **核心观点**：列举视频中的关键观点
3. **典型案例**：整理视频中的案例
4. **识别方法**：如果有，总结识别/判断方法
5. **防骗建议**：如果有，总结建议要点
6. **核心金句**：提炼视频中的关键语句

格式：Markdown，结构清晰，包含列表和表格。
"""
    
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 3000,
        "temperature": 0.7
    }
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    if verbose:
        print(f"📡 调用 GLM API...")
        print(f"📝 输入长度：{len(transcript)} 字符")
    
    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        response.raise_for_status()
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            note_content = result['choices'][0]['message']['content']
            
            if verbose:
                print(f"✅ API 调用成功")
                print(f"📄 输出长度：{len(note_content)} 字符")
            
            return note_content
        else:
            print(f"❌ API 返回异常：{result}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ API 请求超时")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ API 请求失败：{e}")
        return None
    except Exception as e:
        print(f"❌ 生成笔记出错：{e}")
        return None


if __name__ == "__main__":
    # 测试
    import json
    from pathlib import Path
    
    if len(sys.argv) < 2:
        print("用法：python src/summarizer.py <转录文件路径>")
        sys.exit(1)
    
    # 读取转录文件
    transcript_path = Path(sys.argv[1])
    if not transcript_path.exists():
        print(f"❌ 文件不存在：{transcript_path}")
        sys.exit(1)
    
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript = f.read()
    
    # 加载 GLM 配置
    config_path = Path("config/glm-config.json")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            glm_config = json.load(f)
    else:
        print("❌ 配置文件不存在：config/glm-config.json")
        sys.exit(1)
    
    # 生成笔记
    note = generate_note(transcript, glm_config, verbose=True)
    if note:
        print("\n" + "=" * 60)
        print("生成的笔记预览:")
        print("=" * 60)
        print(note[:1000])  # 显示前 1000 字符
        print("...")
    else:
        print("❌ 生成失败")
