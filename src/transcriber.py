#!/usr/bin/env python3
"""
语音转录模块 - 使用 Whisper 进行语音识别
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional


def transcribe_audio(
    audio_path: str,
    output_dir: str,
    verbose: bool = False
) -> Optional[str]:
    """
    使用 Whisper 转录音频
    
    Args:
        audio_path: 音频文件路径
        output_dir: 输出目录
        verbose: 是否显示详细输出
    
    Returns:
        转录文本文件路径，失败返回 None
    """
    
    # 检查音频文件
    if not Path(audio_path).exists():
        print(f"❌ 音频文件不存在：{audio_path}")
        return None
    
    # 检查虚拟环境
    venv_paths = [
        Path.home() / ".openclaw" / "venv",
        Path("./venv"),
        Path("../venv")
    ]
    
    whisper_cmd = None
    for venv_path in venv_paths:
        whisper_bin = venv_path / "bin" / "whisper"
        if whisper_bin.exists():
            whisper_cmd = str(whisper_bin)
            break
    
    if not whisper_cmd:
        # 尝试直接使用系统命令
        whisper_cmd = "whisper"
        print("⚠️  未找到虚拟环境中的 Whisper，尝试使用系统命令")
    
    # 构建 Whisper 命令
    output_template = str(Path(output_dir) / "%(name)s")
    
    cmd = [
        whisper_cmd,
        audio_path,
        "--language", "Chinese",
        "--model", "small",
        "--output_dir", output_dir,
        "--output_format", "txt"
    ]
    
    if verbose:
        print(f"🔧 执行命令：{' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=not verbose,
            text=True,
            timeout=600  # 10 分钟超时
        )
        
        if result.returncode != 0:
            print(f"❌ 转录失败：{result.stderr}")
            return None
        
        # 查找生成的文件
        audio_file = Path(audio_path)
        txt_file = Path(output_dir) / f"{audio_file.stem}.txt"
        
        if txt_file.exists():
            return str(txt_file)
        
        print("❌ 未找到转录文本文件")
        return None
        
    except subprocess.TimeoutExpired:
        print("❌ 转录超时（>10 分钟）")
        return None
    except Exception as e:
        print(f"❌ 转录出错：{e}")
        return None


if __name__ == "__main__":
    # 测试
    if len(sys.argv) < 2:
        print("用法：python src/transcriber.py <音频文件路径>")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    output_dir = "./output"
    
    result = transcribe_audio(audio_path, output_dir, verbose=True)
    if result:
        print(f"✅ 转录成功：{result}")
        # 显示前 10 行
        with open(result, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:10]
            print("\n转录预览:")
            for line in lines:
                print(line.strip())
    else:
        print("❌ 转录失败")
