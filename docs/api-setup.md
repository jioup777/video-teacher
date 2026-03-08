# GLM API 配置指南

本项目使用智谱 AI 的 GLM-4-Flash 模型生成学习笔记。

## 获取 API Key

1. 访问智谱 AI 开放平台：https://open.bigmodel.cn/

2. 注册/登录账号

3. 进入 **控制台** → **API Key 管理**

4. 点击 **创建 API Key**

5. 复制 API Key（格式类似：`xxxxx.xxxxx`）

---

## 配置 API Key

1. 复制配置文件：
```bash
cp config/glm-config.example.json config/glm-config.json
```

2. 编辑 `config/glm-config.json`：
```json
{
  "api_key": "你的 API_KEY",
  "model": "glm-4-Flash",
  "enabled": true
}
```

---

## 免费额度

- **免费额度**：约 100 万 tokens/月
- **超出后**：按量计费（约 0.001 元/千 tokens）
- **处理成本**：
  - 3 分钟视频：~3000 tokens（约 0.003 元）
  - 12 分钟视频：~10000 tokens（约 0.01 元）

---

## 测试 API

```bash
python -c "
import requests
api_key = '你的 API_KEY'
response = requests.post(
    'https://open.bigmodel.cn/api/paas/v4/chat/completions',
    headers={'Authorization': f'Bearer {api_key}'},
    json={'model': 'glm-4-Flash', 'messages': [{'role': 'user', 'content': 'Hello'}]}
)
print(response.json())
"
```

如果返回包含 `choices` 的 JSON，说明 API Key 有效。

---

## 可用模型

| 模型 | 速度 | 质量 | 价格 | 推荐场景 |
|------|------|------|------|---------|
| glm-4-Flash | ⚡⚡⚡ | ⭐⭐⭐ | 💰 | 日常使用（推荐） |
| glm-4 | ⚡⚡ | ⭐⭐⭐⭐ | 💰💰 | 高质量需求 |
| glm-4-Long | ⚡ | ⭐⭐⭐⭐ | 💰💰💰 | 长文本处理 |

---

## 常见问题

### Q: API Key 无效？

检查是否复制完整（包含点号前后的所有字符）。

### Q: 额度用完了怎么办？

1. 等待下个月重置
2. 或充值继续使用

### Q: 可以更换其他模型吗？

可以，修改 `config/glm-config.json` 中的 `model` 字段。
