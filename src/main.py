#!/usr/bin/env python3
"""
B 站视频学习笔记自动生成器 - 主入口

用法:
    python src/main.py --url "https://www.bilibili.com/video/BVxxxxx"
"""

import argparse
import json
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.downloader import download_audio
from src.transcriber import transcribe_audio
from src.summarizer import generate_note
from src.uploader import upload_to_feishu


def load_config(config_name: str) -> dict:
    """加载配置文件"""
    config_path = project_root / "config" / config_name
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def main():
    parser = argparse.ArgumentParser(
        description="B 站视频学习笔记自动生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python src/main.py --url "https://www.bilibili.com/video/BV1g24FzKEfR/"
    python src/main.py --url "https://www.bilibili.com/video/BVxxxxx" --output-dir ./notes
    python src/main.py --url "https://www.bilibili.com/video/BVxxxxx" --upload-to-feishu
        """
    )
    
    parser.add_argument(
        "--url", "-u",
        required=True,
        help="B 站视频链接"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="./output",
        help="输出目录（默认：./output）"
    )
    parser.add_argument(
        "--cookies-path",
        default=None,
        help="B 站 cookies.txt 路径（默认：~/.openclaw/workspace/skills/bilibili-study/cookies.txt）"
    )
    parser.add_argument(
        "--upload-to-feishu",
        action="store_true",
        help="是否上传到飞书文档"
    )
    parser.add_argument(
        "--feishu-space-id",
        default=None,
        help="飞书 Space ID（不指定则使用配置文件）"
    )
    parser.add_argument(
        "--feishu-parent-token",
        default=None,
        help="飞书父节点 Token（不指定则使用配置文件）"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细输出"
    )
    
    args = parser.parse_args()
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 提取 BV 号
    import re
    bvid_match = re.search(r'BV\w+', args.url)
    if not bvid_match:
        print("❌ 无法从链接中提取 BV 号")
        sys.exit(1)
    
    bvid = bvid_match.group()
    print(f"📺 处理视频：{bvid}")
    print(f"🔗 视频链接：{args.url}")
    print()
    
    # 1. 下载音频
    print("=" * 60)
    print("步骤 1/4: 下载音频")
    print("=" * 60)
    
    cookies_path = args.cookies_path
    if not cookies_path:
        default_cookies = Path.home() / ".openclaw" / "workspace" / "skills" / "bilibili-study" / "cookies.txt"
        if default_cookies.exists():
            cookies_path = str(default_cookies)
        else:
            print("⚠️ 未找到 cookies.txt，请指定 --cookies-path")
            sys.exit(1)
    
    audio_path = download_audio(args.url, str(output_dir), cookies_path, args.verbose)
    if not audio_path:
        print("❌ 音频下载失败")
        sys.exit(1)
    
    print(f"✅ 音频已下载：{audio_path}")
    print()
    
    # 2. Whisper 转录
    print("=" * 60)
    print("步骤 2/4: Whisper 转录")
    print("=" * 60)
    
    transcript_path = transcribe_audio(audio_path, str(output_dir), args.verbose)
    if not transcript_path:
        print("❌ 转录失败")
        sys.exit(1)
    
    print(f"✅ 转录完成：{transcript_path}")
    print()
    
    # 3. 生成笔记
    print("=" * 60)
    print("步骤 3/4: 生成学习笔记")
    print("=" * 60)
    
    # 读取转录文本
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript = f.read()
    
    # 加载 GLM 配置
    glm_config = load_config("glm-config.json")
    if not glm_config.get("api_key"):
        print("❌ 未配置 GLM API Key，请编辑 config/glm-config.json")
        sys.exit(1)
    
    note_content = generate_note(transcript, glm_config, args.verbose)
    if not note_content:
        print("❌ 笔记生成失败")
        sys.exit(1)
    
    # 保存笔记
    note_path = output_dir / f"{bvid}_note.md"
    with open(note_path, 'w', encoding='utf-8') as f:
        f.write(note_content)
    
    print(f"✅ 笔记已生成：{note_path}")
    print()
    
    # 4. 上传飞书（可选）
    if args.upload_to_feishu:
        print("=" * 60)
        print("步骤 4/4: 上传到飞书文档")
        print("=" * 60)
        
        # 加载飞书配置
        feishu_config = load_config("feishu-config.json")
        
        space_id = args.feishu_space_id or feishu_config.get("space_id")
        parent_token = args.feishu_parent_token or feishu_config.get("parent_node_token")
        
        if not space_id or not parent_token:
            print("❌ 未配置飞书 Space ID 和 Parent Token")
            print("请编辑 config/feishu-config.json 或使用 --feishu-space-id 和 --feishu-parent-token 参数")
            sys.exit(1)
        
        # 这里需要实现飞书上传逻辑
        # 由于飞书 API 需要额外的依赖，这里仅做示例
        print("⚠️  飞书上传功能需要额外的 API 配置")
        print("💡 请参考 docs/feishu-setup.md 进行配置")
        
        # 实际使用时，调用 upload_to_feishu 函数
        # feishu_url = upload_to_feishu(note_content, space_id, parent_token)
        # print(f"✅ 已上传到飞书：{feishu_url}")
    else:
        print("=" * 60)
        print("处理完成！")
        print("=" * 60)
    
    print()
    print(f"📁 输出目录：{output_dir}")
    print(f"📄 笔记文件：{note_path}")
    print()
    print("✨ 完成！")


if __name__ == "__main__":
    main()
