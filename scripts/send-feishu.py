#!/usr/bin/env python3
"""
飞书消息推送脚本
支持 JSON 和 Markdown 格式
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def extract_articles_from_topics(data: Dict) -> List[Dict]:
    """从topics结构中提取所有文章"""
    articles = []
    topics = data.get("topics", {})
    
    for topic_id, topic_data in topics.items():
        if isinstance(topic_data, dict) and "articles" in topic_data:
            for article in topic_data["articles"]:
                # 添加topic标签
                if isinstance(article, dict):
                    article_copy = article.copy()
                    article_copy["topic"] = topic_id
                    articles.append(article_copy)
    
    return articles


def format_as_markdown(data: Dict) -> str:
    """将数据格式化为 Markdown"""
    lines = []
    
    # 标题
    lines.append("# 📰 每日科技新闻摘要")
    lines.append(f"\n**日期:** {datetime.now().strftime('%Y年%m月%d日')}")
    lines.append(f"**时间范围:** 过去 24 小时")
    lines.append("")
    
    # 统计信息 - 支持两种数据结构
    if "topics" in data:
        # 新的topics结构
        articles = extract_articles_from_topics(data)
        stats = data.get("output_stats", {})
        lines.append("## 📊 统计")
        lines.append(f"- RSS 文章: {stats.get('total_articles', len(articles))} 篇")
        lines.append(f"- Topics: {stats.get('topics_count', len(data.get('topics', {})))} 个")
    else:
        # 旧的articles数组结构
        articles = data.get("articles", [])
        lines.append("## 📊 统计")
        lines.append(f"- RSS 文章: {len(articles)} 篇")
    
    videos = data.get("videos", [])
    if videos:
        lines.append(f"- YouTube 视频: {len(videos)} 个")
    
    lines.append("## 📊 统计")
    lines.append(f"- RSS 文章: {len(articles)} 篇")
    lines.append(f"- YouTube 视频: {len(videos)} 个")
    lines.append("")
    
    # RSS 文章（如果有）
    if articles:
        lines.append("## 📰 RSS 资讯")
        lines.append("")
        
        # 按来源分组
        sources = {}
        for article in articles[:20]:  # 最多显示 20 篇
            source = article.get("source", "Unknown")
            if source not in sources:
                sources[source] = []
            sources[source].append(article)
        
        for source, source_articles in sources.items():
            lines.append(f"### {source}")
            for article in source_articles[:5]:  # 每个来源最多 5 篇
                title = article.get("title", "无标题")
                url = article.get("url", "")
                summary = article.get("summary", "")[:100]
                
                if url:
                    lines.append(f"- [{title}]({url})")
                else:
                    lines.append(f"- {title}")
                
                if summary:
                    lines.append(f"  - {summary}...")
            lines.append("")
    
    # YouTube 视频（如果有）
    if videos:
        lines.append("## 🎬 YouTube 视频")
        lines.append("")
        
        for video in videos:
            title = video.get("title", "无标题")
            channel = video.get("channel", "Unknown")
            url = video.get("url", "")
            transcript_preview = ""
            
            if "transcript" in video and video["transcript"]:
                # 提取转录文本的前 200 字符
                transcript_text = " ".join([
                    seg.get("text", "") 
                    for seg in video["transcript"][:3]
                ])
                transcript_preview = transcript_text[:200]
            
            if url:
                lines.append(f"### [{title}]({url})")
            else:
                lines.append(f"### {title}")
            
            lines.append(f"- **频道:** {channel}")
            if transcript_preview:
                lines.append(f"- **摘要:** {transcript_preview}...")
            lines.append("")
    
    # 页脚
    lines.append("---")
    lines.append("*由 OpenClaw 自动收集整理*")
    
    return "\n".join(lines)


def format_as_simple_markdown(data: Dict) -> str:
    """简化版 Markdown 格式（适合快速预览）"""
    lines = []
    
    lines.append("# 📰 每日科技新闻摘要")
    lines.append(f"\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    
    articles = data.get("articles", [])
    videos = data.get("videos", [])
    
    if articles:
        lines.append(f"## 📊 收集到 {len(articles)} 篇文章")
        lines.append("")
        
        for i, article in enumerate(articles[:10], 1):
            title = article.get("title", "无标题")
            source = article.get("source", "")
            lines.append(f"{i}. {title}")
            if source:
                lines.append(f"   - 来源: {source}")
        lines.append("")
    
    if videos:
        lines.append(f"## 🎬 收集到 {len(videos)} 个视频")
        lines.append("")
        
        for video in videos:
            title = video.get("title", "无标题")
            channel = video.get("channel", "")
            lines.append(f"- {title}")
            if channel:
                lines.append(f"  - 频道: {channel}")
        lines.append("")
    
    lines.append("\n---\n*OpenClaw 自动推送*")
    
    return "\n".join(lines)


def read_file(file_path: str) -> str:
    """读取文件内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def parse_json_file(file_path: str) -> Dict:
    """解析 JSON 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def send_via_webhook(webhook_url: str, message: str, msg_type: str = "text"):
    """通过 Webhook 发送消息"""
    import requests
    
    payload = {
        "msg_type": "post" if msg_type == "markdown" else "text",
        "content": {
            "post" if msg_type == "markdown" else "text": message
        } if msg_type == "text" else {
            "post": {
                "zh_cn": {
                    "title": "每日科技新闻摘要",
                    "content": [[{"tag": "text", "text": message}]]
                }
            }
        }
    }
    
    response = requests.post(webhook_url, json=payload)
    response.raise_for_status()
    
    return response.json()


def main():
    parser = argparse.ArgumentParser(description="推送消息到飞书")
    parser.add_argument(
        "file",
        help="要推送的文件路径（JSON 或 Markdown）"
    )
    parser.add_argument(
        "--type",
        choices=["json", "markdown"],
        default="json",
        help="文件类型"
    )
    parser.add_argument(
        "--webhook",
        help="飞书 Webhook URL（可选，如果不提供则打印到标准输出）"
    )
    parser.add_argument(
        "--format",
        choices=["full", "simple"],
        default="simple",
        help="输出格式（仅对 JSON 有效）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅打印消息，不实际发送"
    )
    
    args = parser.parse_args()
    
    # 读取文件
    if not os.path.exists(args.file):
        print(f"❌ 文件不存在: {args.file}")
        sys.exit(1)
    
    print(f"📄 读取文件: {args.file}")
    
    # 格式化消息
    if args.type == "json":
        data = parse_json_file(args.file)
        
        if args.format == "full":
            message = format_as_markdown(data)
        else:
            message = format_as_simple_markdown(data)
    else:
        message = read_file(args.file)
    
    # 发送或打印
    if args.dry_run or not args.webhook:
        print("\n" + "="*60)
        print("消息预览:")
        print("="*60)
        print(message)
        print("="*60)
        
        if not args.webhook:
            print("\n⚠️ 未提供 Webhook URL，仅打印消息")
            print("💡 使用 --webhook 参数指定飞书 Webhook URL")
    else:
        print(f"\n📤 发送消息到飞书...")
        
        try:
            result = send_via_webhook(args.webhook, message, "markdown")
            print(f"✅ 发送成功: {result}")
        except Exception as e:
            print(f"❌ 发送失败: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
