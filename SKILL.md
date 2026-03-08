---
name: bilibili-video-to-feishu
description: >
  B 站视频学习笔记自动化流程。输入 B 站视频链接，自动完成：
  音频下载 → Whisper 转录 → GLM-4-Flash 整理笔记 → 上传到飞书文档。
  适用于无官方字幕的 B 站视频。
allowed-tools:
  - Read
  - Write
  - Bash
  - feishu_doc
  - feishu_wiki
model: zai/glm-5
---

# B 站视频学习笔记自动化 SKILL

本 SKILL 用于将 B 站视频自动转化为结构化学习笔记并上传到飞书文档。

## 功能特性

- **自动下载音频**：使用 yt-dlp 下载 B 站视频音频
- **语音识别转录**：使用 Whisper（虚拟环境）进行语音转文字
- **智能笔记生成**：使用 GLM-4-Flash 生成结构化学习笔记
- **自动上传飞书**：将笔记上传到飞书文档指定节点

## 环境要求

### 必需环境

1. **虚拟环境**：`~/.openclaw/venv`（已安装 Whisper）
2. **B 站 Cookies**：`/home/ubuntu/.openclaw/workspace/skills/bilibili-study/cookies.txt`
3. **GLM API Key**：`/home/ubuntu/.openclaw/workspace/config/glm-config.json`
4. **飞书配置**：已有 Wiki 节点权限

### 检查环境

```bash
# 检查虚拟环境
source ~/.openclaw/venv/bin/activate && python -c "import whisper; print('✅ Whisper 可用')"

# 检查 Cookies
ls -l /home/ubuntu/.openclaw/workspace/skills/bilibili-study/cookies.txt

# 检查 GLM 配置
cat /home/ubuntu/.openclaw/workspace/config/glm-config.json
```

## 完整流程

### 步骤 1：识别 B 站视频链接

**输入格式**：
- `https://www.bilibili.com/video/BVxxxxx`
- `https://www.bilibili.com/video/BVxxxxx/?spm_id_from=xxx`

**提取视频 ID**：
```bash
video_url="https://www.bilibili.com/video/BV1g24FzKEfR/"
bvid=$(echo "$video_url" | grep -oP 'BV\w+')
echo "视频 ID: $bvid"
```

### 步骤 2：下载音频

**命令**：
```bash
yt-dlp --cookies /home/ubuntu/.openclaw/workspace/skills/bilibili-study/cookies.txt \
  -f "bestaudio" \
  -o "/tmp/bilibili_${bvid}.%(ext)s" \
  "$video_url"
```

**输出**：`/tmp/bilibili_{BV 号}.m4a`

### 步骤 3：Whisper 转录

**⚠️ 关键：必须使用虚拟环境**

```bash
source ~/.openclaw/venv/bin/activate

whisper /tmp/bilibili_${bvid}.m4a \
  --language Chinese \
  --model base \
  --output_dir /tmp/ \
  --output_format txt
```

**输出**：`/tmp/bilibili_{BV 号}.txt`

### 步骤 4：GLM-4-Flash 生成笔记

```python
import requests

api_key = "d3b7abe3f5094404bc922c3207381e2f.rEOUkrriaMfzYKSd"
url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

prompt = f"""你是一位专业的学习笔记整理专家。以下是视频的语音转录文本，请整理成结构化的学习笔记。

**转录文本**：
{transcript}

**输出要求**：
1. 核心主题
2. 核心观点
3. 典型案例
4. 识别方法
5. 防骗建议
6. 核心金句

格式：Markdown，结构清晰。
"""

response = requests.post(
    url,
    headers={'Authorization': f'Bearer {api_key}'},
    json={'model': 'glm-4-Flash', 'messages': [{'role': 'user', 'content': prompt}]}
)
note = response.json()['choices'][0]['message']['content']
```

### 步骤 5：上传飞书文档

```bash
# 创建飞书文档节点
feishu_wiki create \
  --title "{视频标题}" \
  --parent_node_token "I1GtwmgL4iok6WkfOghcR1uwnld" \
  --space_id "7566441763399581724"

# 写入笔记内容
feishu_doc write \
  --doc_token "{新建文档的 token}" \
  --content "{笔记内容}"
```

## 使用示例

### 在 OpenClaw 中使用

```
帮我分析这个 B 站视频：https://www.bilibili.com/video/BV1g24FzKEfR/
```

系统会自动完成所有步骤，返回飞书文档链接。

### 命令行使用

```bash
cd /home/ubuntu/.openclaw/workspace/github/bilibili-video-processor

python src/main.py \
  --url "https://www.bilibili.com/video/BV1g24FzKEfR/" \
  --upload-to-feishu
```

## 性能数据

| 视频时长 | 下载 | 转录 | 生成 | 上传 | 总计 |
|---------|------|------|------|------|------|
| 3 分钟 | 10s | 60s | 5s | 3s | ~80s |
| 12 分钟 | 30s | 180s | 10s | 5s | ~230s |

**Token 消耗**：
- 3 分钟视频：~3000 tokens（约 0.003 元）
- 12 分钟视频：~10000 tokens（约 0.01 元）

## 常见问题

### Q1：Whisper 转录很慢？

使用更小的模型：`--model tiny`（更快，准确度稍低）

### Q2：转录文本有很多识别错误？

在 GLM 提示词中明确要求纠正错误，或提供常见错误的纠正示例。

### Q3：飞书上传失败？

确认有 Wiki 节点写入权限，检查 space_id 和 parent_node_token 正确。

### Q4：虚拟环境找不到？

```bash
ls -la ~/.openclaw/venv/bin/activate
source ~/.openclaw/venv/bin/activate
python -c "import whisper; print('✅')"
```

## 相关资源

- **B 站 Cookies 获取**：`docs/cookies.md`
- **GLM API 文档**：https://open.bigmodel.cn/dev/api
- **Whisper 文档**：https://github.com/openai/whisper
- **飞书文档 API**：https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document

---

*本 SKILL 由 OpenClaw 自动生成 | 最后更新：2026-03-08*
