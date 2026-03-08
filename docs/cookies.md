# B 站 Cookies 获取指南

B 站部分视频需要登录才能下载高质量音频，因此需要提供 Cookies。

## 方法 1：使用浏览器扩展（推荐）

### Chrome/Edge

1. 安装扩展：**Get cookies.txt LOCALLY**
   - Chrome 商店：https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc

2. 访问 B 站并登录：https://www.bilibili.com

3. 点击扩展图标，选择 `Export cookies.txt`

4. 将下载的 `cookies.txt` 文件放到项目根目录

### Firefox

1. 安装扩展：**cookies.txt**
   - Firefox 商店：https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/

2. 访问 B 站并登录

3. 点击扩展图标，导出 cookies.txt

---

## 方法 2：使用开发者工具

1. 访问 B 站并登录：https://www.bilibili.com

2. 按 `F12` 打开开发者工具

3. 切换到 **Application**（或 **存储**）标签

4. 左侧展开 **Cookies** → 选择 `https://www.bilibili.com`

5. 复制所有 Cookies，保存为 `cookies.txt` 文件

---

## 方法 3：从 OpenClaw 现有配置复制

如果你已经在使用 OpenClaw 的 bilibili-study 技能：

```bash
cp ~/.openclaw/workspace/skills/bilibili-study/cookies.txt ./cookies.txt
```

---

## 验证 Cookies

```bash
# 测试 Cookies 是否有效
yt-dlp --cookies cookies.txt "https://www.bilibili.com/video/BVxxxxx" --simulate
```

如果输出视频信息，说明 Cookies 有效。

---

## 注意事项

1. **Cookies 会过期**：建议每 1-2 个月更新一次
2. **不要分享 Cookies**：包含登录信息，不要上传到 GitHub
3. **已添加到 .gitignore**：项目已配置忽略 cookies.txt 文件

---

## 常见问题

### Q: Cookies 无效怎么办？

重新登录 B 站，然后重新导出 Cookies。

### Q: 没有 cookies.txt 能用吗？

可以，但部分视频可能无法下载高质量音频。

### Q: Cookies 文件应该放在哪里？

- 项目根目录（推荐）
- 或者使用 `--cookies-path` 参数指定路径
