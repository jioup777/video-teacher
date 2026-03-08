#!/usr/bin/env python3
"""
飞书消息推送脚本
支持 JSON 和 Markdown 格式，支持 topics 结构
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def extract_articles_from_topics(data: Dict) -> List[Dict]:
    """从 topics 结构中提取所有文章"""
    articles = []
    topics = data.get("topics", {})
    
    for topic_id, topic_data in topics.items():
        if isinstance(topic_data, dict) and "articles" in topic_data:
            for article in topic_data["articles"]:
                if isinstance(article, dict):
                    article_copy = article.copy()
                    article_copy["topic"] = topic_id
                    articles.append(article_copy)
    
    return articles


def format_as_markdown(data: Dict) -> str:
    """将数据格式化为 Markdown（完整版）"""
    lines = []
    
    lines.append("# 📰 每日科技新闻摘要")
    lines.append(f"\n**日期:** {datetime.now().strftime('%Y年%m月%d日')}")
    lines.append(f"**时间范围:** 过去 24 小时")
    lines.append("")
    
    # 统计信息
    if "topics" in data:
        articles = extract_articles_from_topics(data)
        stats = data.get("output_stats", {})
        lines.append("## 📊 统计")
        lines.append(f"- RSS 文章：{stats.get('total_articles', len(articles))} 篇")
        lines.append(f"- Topics: {stats.get('topics_count', len(data.get('topics', {})))} 个")
    else:
        articles = data.get("articles", [])
        lines.append("## 📊 统计")
        lines.append(f"- RSS 文章：{len(articles)} 篇")
    
    videos = data.get("videos", [])
    if videos:
        lines.append(f"- YouTube 视频：{len(videos)} 个")
    lines.append("")
    
    # 按主题分组显示文章
    if "topics" in data:
        topics = data.get("topics", {})
        for topic_id, topic_data in topics.items():
            topic_articles = topic_data.get("articles", [])[:5]
            if topic_articles:
                lines.append(f"## {topic_id.upper()}")
                lines.append("")
                for article in topic_articles:
                    title = article.get("title", "无标题")
                    url = article.get("link") or article.get("url", "")
                    source = article.get("source_name", "")
                    
                    if url:
                        lines.append(f"- [{title}]({url})")
                    else:
                        lines.append(f"- {title}")
                    if source:
                        lines.append(f"  - 来源：{source}")
                lines.append("")
    elif articles:
        lines.append("## 📰 RSS 资讯")
        lines.append("")
        sources = {}
        for article in articles[:20]:
            source = article.get("source", "Unknown")
            if source not in sources:
                sources[source] = []
            sources[source].append(article)
        
        for source, source_articles in sources.items():
            lines.append(f"### {source}")
            for article in source_articles[:5]:
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
    
    # YouTube 视频
    if videos:
        lines.append("## 🎬 YouTube 视频")
        lines.append("")
        
        for video in videos:
            title = video.get("title", "无标题")
            channel = video.get("channel", "Unknown")
            url = video.get("url", "")
            
            if url:
                lines.append(f"### [{title}]({url})")
            else:
                lines.append(f"### {title}")
            
            lines.append(f"- **频道:** {channel}")
            
            if "transcript" in video and video["transcript"]:
                transcript_text = " ".join([seg.get("text", "") for seg in video["transcript"][:3]])
                lines.append(f"- **摘要:** {transcript_text[:200]}...")
            lines.append("")
    
    lines.append("---")
    lines.append("*由 OpenClaw 自动收集整理*")
    
    return "\n".join(lines)


def format_as_simple_markdown(data: Dict) -> str:
    """简化版 Markdown 格式（适合快速预览）"""
    lines = []
    
    lines.append("# 📰 每日科技新闻摘要")
    lines.append(f"\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    
    # 支持两种数据结构
    if "topics" in data:
        articles = extract_articles_from_topics(data)
        stats = data.get("output_stats", {})
        lines.append(f"## 📊 共 {stats.get('total_articles', len(articles))} 篇文章 | {len(data.get('videos', []))} 个视频")
    else:
        articles = data.get("articles", [])
        lines.append(f"## 📊 共 {len(articles)} 篇文章 | {len(data.get('videos', []))} 个视频")
    
    videos = data.get("videos", [])
    
    # 按主题分组显示文章
    if "topics" in data:
        lines.append("")
        topics = data.get("topics", {})
        for topic_id, topic_data in topics.items():
            topic_articles = topic_data.get("articles", [])[:5]
            if topic_articles:
                lines.append(f"## {topic_id.upper()}")
                lines.append("")
                for article in topic_articles:
                    title = article.get("title", "无标题")
                    url = article.get("link") or article.get("url", "")
                    source = article.get("source_name", "")
                    
                    if url:
                        lines.append(f"- [{title}]({url})")
                    else:
                        lines.append(f"- {title}")
                    if source:
                        lines.append(f"  - 来源：{source}")
                lines.append("")
    elif articles:
        lines.append(f"\n## 📰 精选文章")
        lines.append("")
        
        for i, article in enumerate(articles[:10], 1):
            title = article.get("title", "无标题")
            url = article.get("link") or article.get("url", "")
            source = article.get("source", "")
            
            if url:
                lines.append(f"{i}. [{title}]({url})")
            else:
                lines.append(f"{i}. {title}")
            if source:
                lines.append(f"   - 来源：{source}")
        lines.append("")
    
    # YouTube 视频
    if videos:
        lines.append("## 🎬 YouTube 视频")
        lines.append("")
        
        for video in videos:
            title = video.get("title", "无标题")
            channel = video.get("channel", "")
            url = video.get("url", "")
            
            if url:
                lines.append(f"- [{title}]({url})")
            else:
                lines.append(f"- {title}")
            if channel:
                lines.append(f"  - 频道：{channel}")
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


def send_via_webhook(webhook_url: str, message: str, msg_type: str = "post"):
    """通过 Webhook 发送消息到飞书"""
    import requests
    
    # 飞书开放平台 post 消息格式
    payload = {
        "msg_type": "post",
        "content": {
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
        print(f"❌ 文件不存在：{args.file}")
        sys.exit(1)
    
    print(f"📄 读取文件：{args.file}")
    
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
            result = send_via_webhook(args.webhook, message, "post")
            print(f"✅ 发送成功：{result}")
        except Exception as e:
            print(f"❌ 发送失败：{e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
