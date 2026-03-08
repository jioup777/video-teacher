#!/usr/bin/env python3
"""
使用 GLM-4.7 翻译科技新闻摘要为中文
"""

import argparse
import json
import os
import sys
from typing import Dict, List


def translate_with_glm(text: str, context: str = "科技新闻标题") -> str:
    """调用 GLM-4.7 翻译文本"""
    import requests
    
    # 从环境变量或配置文件读取 API Key
    api_key = os.environ.get('GLM_API_KEY', '')
    if not api_key:
        # 尝试从配置文件读取
        config_path = os.path.expanduser('~/.openclaw/workspace/config/glm-config.json')
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = json.load(f)
                api_key = config.get('api_key', '')
    
    if not api_key:
        print(f"⚠️ 未配置 GLM API Key，返回原文")
        return text
    
    prompt = f"""请将以下{context}翻译成中文，要求：
1. 准确传达原意
2. 符合中文表达习惯
3. 保留专有名词（如产品名、公司名）的原文
4. 简洁明了

原文：{text}

中文翻译："""
    
    try:
        response = requests.post(
            'https://open.bigmodel.cn/api/paas/v4/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'glm-4-flash',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 200,
                'temperature': 0.3
            },
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"⚠️ 翻译失败：{e}")
        return text


def translate_article(article: Dict, translate_summary: bool = False) -> Dict:
    """翻译单篇文章"""
    translated = article.copy()
    
    # 翻译标题
    title = article.get('title', '')
    if title:
        translated['title_zh'] = translate_with_glm(title, "科技新闻标题")
    
    # 可选：翻译摘要
    if translate_summary:
        summary = article.get('summary', '') or article.get('snippet', '')
        if summary:
            translated['summary_zh'] = translate_with_glm(summary[:300], "科技新闻摘要")
    
    return translated


def translate_video(video: Dict) -> Dict:
    """翻译视频信息"""
    translated = video.copy()
    
    title = video.get('title', '')
    if title:
        translated['title_zh'] = translate_with_glm(title, "YouTube 视频标题")
    
    return translated


def process_data(data: Dict, translate_summaries: bool = False) -> Dict:
    """处理整个数据集"""
    result = data.copy()
    
    # 翻译 topics 中的文章
    if "topics" in result:
        translated_topics = {}
        for topic_id, topic_data in result["topics"].items():
            translated_topic = topic_data.copy()
            articles = topic_data.get("articles", [])
            translated_articles = [translate_article(a, translate_summaries) for a in articles]
            translated_topic["articles"] = translated_articles
            translated_topics[topic_id] = translated_topic
        result["topics"] = translated_topics
    
    # 翻译 videos
    if "videos" in result:
        videos = result["videos"]
        result["videos"] = [translate_video(v) for v in videos]
    
    return result


def format_as_chinese_markdown(data: Dict) -> str:
    """格式化为中文 Markdown"""
    lines = []
    
    lines.append("# 📰 每日科技新闻摘要")
    lines.append(f"\n📅 {data.get('generated', '')[:10]}")
    lines.append("")
    
    # 统计
    if "topics" in data:
        stats = data.get("output_stats", {})
        lines.append(f"**共 {stats.get('total_articles', 0)} 篇文章 | {len(data.get('videos', []))} 个视频**")
    lines.append("")
    
    # 按主题显示
    if "topics" in data:
        for topic_id, topic_data in data["topics"].items():
            articles = topic_data.get("articles", [])[:5]
            if articles:
                # 翻译主题名
                topic_names = {
                    'ai-agent': '🤖 AI 智能体',
                    'frontier-tech': '🚀 前沿科技',
                    'crypto': '💰 加密货币',
                    'llm': '🧠 大语言模型'
                }
                topic_name = topic_names.get(topic_id, topic_id.upper())
                
                lines.append(f"## {topic_name}")
                lines.append("")
                
                for article in articles:
                    title_zh = article.get('title_zh', article.get('title', '无标题'))
                    title_en = article.get('title', '')
                    url = article.get("link") or article.get("url", "")
                    source = article.get("source_name", "")
                    
                    if url:
                        lines.append(f"- **{title_zh}**")
                        lines.append(f"  - 原文：[{title_en}]({url})")
                    else:
                        lines.append(f"- {title_zh}")
                    
                    if source:
                        lines.append(f"  - 来源：{source}")
                    
                    # 显示中文摘要（如果有）
                    summary_zh = article.get('summary_zh', '')
                    if summary_zh:
                        lines.append(f"  - {summary_zh}")
                    
                    lines.append("")
    
    # YouTube 视频
    if "videos" in data:
        lines.append("## 🎬 YouTube 精选")
        lines.append("")
        
        for video in data["videos"][:6]:
            title_zh = video.get('title_zh', video.get('title', '无标题'))
            title_en = video.get('title', '')
            channel = video.get("channel", "")
            url = video.get("url", "")
            
            if url:
                lines.append(f"- **{title_zh}**")
                lines.append(f"  - [原文]({url}) | 📺 {channel}")
            else:
                lines.append(f"- {title_zh} | 📺 {channel}")
            lines.append("")
    
    lines.append("---")
    lines.append("*由 OpenClaw + GLM-4.7 自动翻译整理*")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="翻译科技新闻摘要为中文")
    parser.add_argument("input", help="输入 JSON 文件路径")
    parser.add_argument("--output", "-o", help="输出文件路径（不指定则打印到控制台）")
    parser.add_argument("--translate-summaries", action="store_true", help="是否翻译摘要内容")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown", help="输出格式")
    
    args = parser.parse_args()
    
    # 读取输入
    if not os.path.exists(args.input):
        print(f"❌ 文件不存在：{args.input}")
        sys.exit(1)
    
    print(f"📄 读取文件：{args.input}")
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 翻译
    print("🔄 开始翻译...")
    translated = process_data(data, args.translate_summaries)
    
    # 输出
    if args.format == "json":
        output_text = json.dumps(translated, ensure_ascii=False, indent=2)
    else:
        output_text = format_as_chinese_markdown(translated)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_text)
        print(f"✅ 已保存到：{args.output}")
    else:
        print("\n" + "="*60)
        print(output_text)
        print("="*60)


if __name__ == "__main__":
    main()
