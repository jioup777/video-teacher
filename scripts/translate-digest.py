#!/usr/bin/env python3
"""
使用 GLM-4-Flash 批量翻译科技新闻摘要为中文
优化：批量翻译，单次请求处理所有标题
"""

import argparse
import json
import os
import sys
import requests
from typing import Dict, List, Tuple


def load_glm_config() -> dict:
    """加载 GLM 配置"""
    config_path = os.path.expanduser('~/.openclaw/workspace/config/glm-config.json')
    if os.path.exists(config_path):
        with open(config_path) as f:
            return json.load(f)
    return {}


def translate_batch_glm(texts: List[str], context: str = "科技新闻标题", batch_size: int = 20) -> List[str]:
    """批量翻译文本列表（分批次请求，避免超时）"""
    config = load_glm_config()
    api_key = config.get('api_key', os.environ.get('GLM_API_KEY', ''))
    model = config.get('model', 'glm-4-Flash')
    
    if not api_key:
        print(f"⚠️ 未配置 GLM API Key，返回原文")
        return texts
    
    all_translations = []
    
    # 分批次处理
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        # 构建批量翻译提示
        numbered_texts = "\n".join([f"{j+1}. {t}" for j, t in enumerate(batch)])
        
        prompt = f"""请将以下{context}批量翻译成中文，要求：
1. 准确传达原意
2. 符合中文表达习惯
3. 保留专有名词（产品名、公司名、人名）原文
4. 简洁明了
5. 按原顺序返回，格式：1. 翻译 1\n2. 翻译 2...

原文：
{numbered_texts}

中文翻译："""
        
        try:
            print(f"  📦 批次 {batch_num}/{total_batches}...")
            response = requests.post(
                'https://open.bigmodel.cn/api/paas/v4/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': model,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': 2000,
                    'temperature': 0.3
                },
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            translated_text = result['choices'][0]['message']['content'].strip()
            
            # 解析返回结果
            batch_translations = []
            for line in translated_text.split('\n'):
                clean = line.strip()
                if not clean:
                    continue
                # 移除开头的序号和"翻译 X："前缀
                # 匹配模式："1. " 或 "1." 或 "翻译 1：" 或 "- "
                import re
                clean = re.sub(r'^\d+[\.,]\s*', '', clean)  # 移除 "1. " 或 "1."
                clean = re.sub(r'^翻译\s*\d+\s*：\s*', '', clean)  # 移除 "翻译 1："
                clean = re.sub(r'^[-•]\s*', '', clean)  # 移除 "- " 或 "• "
                if clean:
                    batch_translations.append(clean)
            
            # 如果解析失败，返回原文
            if len(batch_translations) != len(batch):
                print(f"  ⚠️ 批次 {batch_num} 解析失败，使用原文")
                all_translations.extend(batch)
            else:
                all_translations.extend(batch_translations)
        
        except Exception as e:
            print(f"  ⚠️ 批次 {batch_num} 失败：{e}，使用原文")
            all_translations.extend(batch)
    
    return all_translations


def process_data_batch(data: Dict) -> Dict:
    """批量处理整个数据集"""
    result = data.copy()
    
    # 收集所有需要翻译的标题
    article_map = []  # (topic_id, article_index, title)
    video_titles = []  # (index, title)
    
    # 收集文章标题
    if "topics" in result:
        translated_topics = {}
        for topic_id, topic_data in result["topics"].items():
            translated_topic = topic_data.copy()
            articles = topic_data.get("articles", [])
            for i, article in enumerate(articles):
                title = article.get('title', '')
                if title:
                    article_map.append((topic_id, i, title))
            translated_topics[topic_id] = translated_topic
        result["topics"] = translated_topics
    
    # 收集视频标题
    if "videos" in result:
        for i, video in enumerate(result["videos"]):
            title = video.get('title', '')
            if title:
                video_titles.append((i, title))
    
    # 批量翻译文章标题
    print(f"📝 翻译 {len(article_map)} 篇文章标题...")
    if article_map:
        titles_to_translate = [t[2] for t in article_map]
        translated = translate_batch_glm(titles_to_translate, "科技新闻标题")
        
        # 回填翻译结果
        for (topic_id, idx, _), zh_title in zip(article_map, translated):
            result["topics"][topic_id]["articles"][idx]["title_zh"] = zh_title
        print(f"✅ 文章翻译完成")
    
    # 批量翻译视频标题
    print(f"📝 翻译 {len(video_titles)} 个视频标题...")
    if video_titles:
        titles_to_translate = [t[1] for t in video_titles]
        translated = translate_batch_glm(titles_to_translate, "YouTube 视频标题")
        
        # 回填翻译结果
        for (idx, _), zh_title in zip(video_titles, translated):
            result["videos"][idx]["title_zh"] = zh_title
        print(f"✅ 视频翻译完成")
    
    return result


def format_as_chinese_markdown(data: Dict) -> str:
    """格式化为中文 Markdown"""
    lines = []
    
    from datetime import datetime
    lines.append("# 📰 每日科技新闻摘要")
    lines.append(f"\n📅 {datetime.now().strftime('%Y年%m月%d日')}")
    lines.append("")
    
    # 统计
    if "topics" in data:
        stats = data.get("output_stats", {})
        lines.append(f"**共 {stats.get('total_articles', 0)} 篇文章 | {len(data.get('videos', []))} 个视频**")
    lines.append("")
    
    # 按主题显示
    if "topics" in data:
        topic_names = {
            'ai-agent': '🤖 AI 智能体',
            'frontier-tech': '🚀 前沿科技',
            'crypto': '💰 加密货币',
            'llm': '🧠 大语言模型'
        }
        
        for topic_id, topic_data in data["topics"].items():
            articles = topic_data.get("articles", [])[:5]
            if articles:
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
                        lines.append(f"  - [原文]({url})")
                    else:
                        lines.append(f"- {title_zh}")
                    
                    if source:
                        lines.append(f"  - 来源：{source}")
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
    lines.append("*由 OpenClaw + GLM-4-Flash 自动翻译整理*")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="批量翻译科技新闻摘要为中文")
    parser.add_argument("input", help="输入 JSON 文件路径")
    parser.add_argument("--output", "-o", help="输出文件路径（不指定则打印到控制台）")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown", help="输出格式")
    
    args = parser.parse_args()
    
    # 读取输入
    if not os.path.exists(args.input):
        print(f"❌ 文件不存在：{args.input}")
        sys.exit(1)
    
    print(f"📄 读取文件：{args.input}")
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 批量翻译
    print("🔄 开始批量翻译...")
    translated = process_data_batch(data)
    
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
