# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## 飞书 Webhook

- **群机器人 Webhook:** `https://open.feishu.cn/open-apis/bot/v2/hook/0f69ce39-2e52-41b3-8a04-dbb76959964c`
- **配置文件:** `config/feishu-webhook.json`
- ⚠️ **重要：** 这是持久化配置，不要再次向用户索取！

---

Add whatever helps you do your job. This is your cheat sheet.

## Feishu

### Webhook URL
- 飞书消息推送：`https://open.feishu.cn/open-apis/bot/v2/hook/0f69ce39-2e52-41b3-8a04-dbb76959964c`

## Supadata API Keys（轮换池）

文档：https://vicyrpffceo.feishu.cn/wiki/EM9awXXMmiPSXXkZal1csHhHnRe
配置文件：`/home/ubuntu/.openclaw/workspace/config/supadata-keys.json`

共 6 个账户（第 7 个待填充），用于 YouTube 频道监控额度轮换（免费计划 100 credits/月/账户）

| 序号 | 邮箱 | API Key |
|------|------|---------|
| 1 | tmljy33@gmail.com | sd_634a90bcf957c3dd39c52c97f1e46e62 |
| 2 | jiouperman777@2925.com | sd_4aa24fbafdf8700e8599b2498f941462 |
| 3 | jiouperman66@2925.com | sd_7d873f6a3baa912ecc580c78715541e2 |
| 4 | jiouperman8@2925.com | sd_2224e6431611410e51d5864b05899973 |
| 5 | jiouperman88@2925.com | sd_44f81832961d5185a4f15c09e4a57a63 |
| 6 | jiouperman77@2925.com | sd_dd8fbad9569fa5f7dfe497ad804dc384 |

**轮换策略：** 当当前账户剩余额度 < 20 credits 时切换到下一个账户
