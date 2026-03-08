#!/usr/bin/env python3
"""
音频下载模块 - 使用 yt-dlp 下载 B 站视频音频
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional


def download_audio(
    video_url: str,
    output_dir: str,
    cookies_path: str,
    verbose: bool = False
) -> Optional[str]:
    """
    下载 B 站视频音频
    
    Args:
        video_url: B 站视频链接
        output_dir: 输出目录
        cookies_path: cookies.txt 路径
        verbose: 是否显示详细输出
    
    Returns:
        音频文件路径，失败返回 None
    """
    
    # 检查 cookies 文件
    if not Path(cookies_path).exists():
        print(f"❌ Cookies 文件不存在：{cookies_path}")
        return None
    
    # 构建 yt-dlp 命令
    output_template = str(Path(output_dir) / "bilibili_%(id)s.%(ext)s")
    
    cmd = [
        "yt-dlp",
        "--cookies", cookies_path,
        "-f", "bestaudio",
        "-o", output_template,
        video_url
    ]
    
    if verbose:
        print(f"🔧 执行命令：{' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=not verbose,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            print(f"❌ 下载失败：{result.stderr}")
            return None
        
        # 查找生成的文件
        import glob
        # 从 URL 提取 BV 号
        import re
        bvid_match = re.search(r'BV\w+', video_url)
        if bvid_match:
            bvid = bvid_match.group()
            audio_files = list(Path(output_dir).glob(f"bilibili_{bvid}.*"))
            if audio_files:
                return str(audio_files[0])
        
        # 如果找不到 BV 号，返回最新的 m4a 文件
        audio_files = list(Path(output_dir).glob("bilibili_*.m4a"))
        if audio_files:
            return str(max(audio_files, key=lambda p: p.stat().st_mtime))
        
        print("❌ 未找到下载的音频文件")
        return None
        
    except subprocess.TimeoutExpired:
        print("❌ 下载超时（>5 分钟）")
        return None
    except Exception as e:
        print(f"❌ 下载出错：{e}")
        return None


if __name__ == "__main__":
    # 测试
    if len(sys.argv) < 2:
        print("用法：python src/downloader.py <视频链接> [cookies 路径]")
        sys.exit(1)
    
    url = sys.argv[1]
    cookies = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not cookies:
        cookies = str(Path.home() / ".openclaw" / "workspace" / "skills" / "bilibili-study" / "cookies.txt")
    
    result = download_audio(url, "./output", cookies, verbose=True)
    if result:
        print(f"✅ 下载成功：{result}")
    else:
        print("❌ 下载失败")
