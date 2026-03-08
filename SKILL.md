---
name: video-to-feishu
description: >
  视频学习笔记自动化流程。自动识别视频来源（B 站/YouTube），
  调用不同策略生成结构化笔记并上传飞书。
  B 站：yt-dlp → Whisper → GLM
  YouTube：Supadata API → GLM
allowed-tools:
  - Read
  - Write
  - Bash
  - feishu_doc
  - feishu_wiki
model: zai/glm-5
---

# 视频学习笔记自动化 SKILL

本 SKILL 用于将 B 站/YouTube 视频自动转化为结构化学习笔记并上传到飞书文档。

## 功能特性

- **自动识别视频来源**：检测 URL 判断是 B 站还是 YouTube
- **B 站处理**：yt-dlp 下载 → Whisper 转录 → GLM 整理
- **YouTube 处理**：Supadata API 获取字幕 → GLM 整理
- **自动上传飞书**：将笔记上传到飞书文档指定节点

---

## 快速开始

### 输入视频链接

支持格式：
- B 站：`https://www.bilibili.com/video/BVxxxxx`
- YouTube：`https://www.youtube.com/watch?v=xxxxx`

### 自动判断流程

```
输入视频链接
    ↓
识别来源（B 站 / YouTube）
    ↓
┌─────────────────┬─────────────────┐
│     B 站        │    YouTube      │
├─────────────────┼─────────────────┤
│ yt-dlp 下载音频  │ Supadata API    │
│ Whisper 转录     │ 获取转录文本     │
│ GLM 整理笔记     │ GLM 整理笔记     │
└─────────────────┴─────────────────┘
    ↓
上传飞书文档
```

---

## 步骤 1：识别视频来源

```bash
video_url="https://www.youtube.com/watch?v=xxxxx"

if [[ "$video_url" == *"bilibili.com"* ]]; then
    source="bilibili"
    video_id=$(echo "$video_url" | grep -oP 'BV\w+')
elif [[ "$video_url" == *"youtube.com"* ]] || [[ "$video_url" == *"youtu.be"* ]]; then
    source="youtube"
    video_id=$(echo "$video_url" | grep -oP '(?<=v=)[^&]+|(?<=youtu\.be/)[^?]+')
else
    echo "❌ 不支持的视频来源"
    exit 1
fi

echo "来源: $source, ID: $video_id"
```

---

## 步骤 2A：B 站处理流程

### 2A-1：下载音频

```bash
yt-dlp --cookies /path/to/cookies.txt \
  -f "bestaudio" \
  -o "/tmp/bilibili_${video_id}.%(ext)s" \
  "$video_url"
```

**输出**：`/tmp/bilibili_{BV号}.m4a`

### 2A-2：Whisper 转录

**⚠️ 关键：必须使用虚拟环境**

```bash
source ~/.openclaw/venv/bin/activate

whisper /tmp/bilibili_${video_id}.m4a \
  --language Chinese \
  --model base \
  --output_dir /tmp/ \
  --output_format txt
```

**输出**：`/tmp/bilibili_{BV号}.txt`

### 2A-3：GLM 整理笔记

```python
import requests

api_key = "YOUR_GLM_API_KEY"  # 从配置文件读取

with open(f'/tmp/bilibili_{video_id}.txt', 'r') as f:
    transcript = f.read()

prompt = f"""你是一位专业的学习笔记整理专家。以下是视频的语音转录文本：

**转录文本**：
{transcript}

**输出要求**：
1. 核心概念：主题的核心概念是什么
2. 核心价值：为什么重要
3. 使用方法：如何使用
4. 对比示例：前后对比
5. 适用场景：哪些场景适用
6. 实用模板：直接可用的模板
7. 底层原理：为什么有效

格式：Markdown，结构清晰，包含代码示例和对比表格。
"""

response = requests.post(
    "https://open.bigmodel.cn/api/paas/v4/chat/completions",
    headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
    json={"model": "glm-4-Flash", "messages": [{"role": "user", "content": prompt}]}
)
note = response.json()['choices'][0]['message']['content']
```

---

## 步骤 2B：YouTube 处理流程

### 2B-1：Supadata API 获取转录

**API 配置**：
- 注册：https://supadata.ai
- 免费额度：100 credits/月
- 监控面板：https://dash.supadata.ai

**获取转录**：
```bash
curl -s "https://api.supadata.ai/v1/youtube/transcript?videoId=${video_id}" \
  -H "X-API-Key: YOUR_SUPADATA_API_KEY" \
  > /tmp/youtube_transcript_${video_id}.json
```

**解析转录文本**：
```python
import json

with open(f'/tmp/youtube_transcript_{video_id}.json', 'r') as f:
    data = json.load(f)

# 提取纯文本
transcript = ''.join([seg['text'] for seg in data['content']])

# 保存为文本文件
with open(f'/tmp/youtube_transcript_{video_id}.txt', 'w') as f:
    f.write(transcript)
```

**输出**：`/tmp/youtube_transcript_{video_id}.txt`

### 2B-2：GLM 整理笔记

```python
import requests

api_key = "YOUR_GLM_API_KEY"  # 从配置文件读取

with open(f'/tmp/youtube_transcript_{video_id}.txt', 'r') as f:
    transcript = f.read()

prompt = f"""请将以下 YouTube 视频转录内容整理成结构化的学习笔记：

要求：
1. 提取核心观点和关键概念
2. 使用 Markdown 格式，包含标题、列表、表格
3. 保持口语化但逻辑清晰
4. 标注视频元信息
5. 输出中文

视频链接：https://www.youtube.com/watch?v={video_id}

转录内容：
{transcript[:18000]}
"""

response = requests.post(
    "https://open.bigmodel.cn/api/paas/v4/chat/completions",
    headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
    json={"model": "glm-4-Flash", "messages": [{"role": "user", "content": prompt}]}
)
note = response.json()['choices'][0]['message']['content']
```

---

## 步骤 3：上传飞书文档

### 飞书配置

- **父节点**：你的飞书知识库节点
- **Space ID**：你的飞书 Space ID

### 创建文档

使用 OpenClaw 的 feishu_doc 工具：

```bash
# 创建飞书文档节点
feishu_doc create \
  --title "{视频标题} - {来源}学习笔记" \
  --folder_token "YOUR_FOLDER_TOKEN"

# 写入笔记内容
feishu_doc write \
  --doc_token "{文档token}" \
  --content "{笔记内容}"
```

---

## 性能对比

| 指标 | B 站（Whisper） | YouTube（Supadata） |
|------|----------------|-------------------|
| 转录速度 | 3-10 分钟 | 5-10 秒 |
| 费用 | 免费 | 1 credit/视频 |
| 准确度 | 依赖音频质量 | 依赖官方字幕 |
| 适用场景 | 无官方字幕 | 有官方字幕 |

---

## 环境要求

### B 站处理

1. **虚拟环境**：安装 Whisper
2. **B 站 Cookies**：用于下载音频
3. **GLM API Key**：智谱 AI

### YouTube 处理

1. **Supadata API Key**：免费 100 credits/月
2. **GLM API Key**：同上

---

## 配置文件示例

### GLM 配置

`config/glm-config.json`:
```json
{
  "api_key": "YOUR_GLM_API_KEY",
  "model": "glm-4-Flash",
  "enabled": true
}
```

### Supadata 配置

`config/supadata-config.json`:
```json
{
  "api_key": "YOUR_SUPADATA_API_KEY",
  "base_url": "https://api.supadata.ai/v1",
  "plan": "Free (100/mo)"
}
```

### 飞书配置

`config/feishu-config.json`:
```json
{
  "space_id": "YOUR_SPACE_ID",
  "parent_node_token": "YOUR_PARENT_NODE_TOKEN",
  "enabled": true
}
```

---

## 常见问题

### Q1：YouTube 转录失败怎么办？

**可能原因**：
- 视频无官方字幕 → 改用 B 站流程（yt-dlp + Whisper）
- API 额度用完 → 检查 Supadata 仪表板

### Q2：Supadata API 额度不足？

**解决方案**：
1. 查看剩余额度
2. 轮换 API Key（多账户）
3. 改用 B 站流程（yt-dlp + Whisper，免费）

### Q3：飞书上传失败？

**检查项**：
1. 确认父节点 Token 正确
2. 确认有写入权限
3. 检查网络连接

---

## 相关资源

- **Supadata API 文档**：https://supadata.ai/docs
- **GLM API 文档**：https://open.bigmodel.cn/dev/api
- **Whisper 文档**：https://github.com/openai/whisper
- **飞书文档 API**：https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document

---

## 开源协议

MIT License

---

*本 SKILL 由 OpenClaw 社区维护 | 最后更新：2026-03-08*
*支持：B 站、YouTube | 自动判断来源*