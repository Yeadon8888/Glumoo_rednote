# Railway 部署指南

本文档介绍如何将 Glumoo 红墨 AI 图文生成器部署到 Railway。

## 🚀 快速部署

### 1. 准备 API Key

访问 [Google AI Studio](https://aistudio.google.com/app/apikey) 获取 Gemini API Key。

> ⚠️ **重要安全提示**：不要将 API Key 提交到 Git 仓库！

### 2. 连接 Railway

1. 访问 [Railway](https://railway.app)
2. 点击 "New Project"
3. 选择 "Deploy from GitHub repo"
4. 选择您的 `Glumoo_rednote` 仓库

### 3. 配置环境变量

在 Railway 项目中添加以下环境变量：

```bash
# 必填：Google Gemini API Key
GOOGLE_API_KEY=your_google_api_key_here

# 可选：如果使用自定义域名，添加到 CORS 允许列表
# CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

**配置步骤：**
1. 在 Railway 项目页面，点击 "Variables" 标签
2. 点击 "New Variable"
3. 输入变量名 `GOOGLE_API_KEY`
4. 输入您的 API Key
5. 点击 "Add"

### 4. 部署

Railway 会自动检测 Dockerfile 并开始构建：
- 构建时间：约 3-5 分钟
- 自动部署：代码推送后自动重新部署
- 健康检查：Railway 会通过 `/api/health` 端点检查服务状态

### 5. 访问应用

部署完成后：
1. 点击 "Settings" → "Domains"
2. 点击 "Generate Domain" 生成公开访问域名
3. 或者绑定自定义域名

## 📋 环境变量说明

| 变量名 | 说明 | 必填 | 示例 |
|--------|------|------|------|
| `GOOGLE_API_KEY` | Google Gemini API Key | ✅ 是 | `AIzaSy...` |
| `GEMINI_API_KEY` | Gemini API Key（备选） | ❌ 否 | `AIzaSy...` |
| `FLASK_DEBUG` | 调试模式 | ❌ 否 | `False` |
| `FLASK_PORT` | 端口号 | ❌ 否 | `12398` |

> 💡 **提示**：`GOOGLE_API_KEY` 和 `GEMINI_API_KEY` 任选其一即可，代码会优先读取 `GOOGLE_API_KEY`。

## 🔧 配置逻辑

应用按以下优先级读取配置：

1. **环境变量**（最高优先级）
   - `GOOGLE_API_KEY` 或 `GEMINI_API_KEY`
   - 适用于 Railway、Render、Fly.io 等云平台

2. **配置文件**
   - `text_providers.yaml`
   - `image_providers.yaml`
   - 如果文件中有 `api_key`，且环境变量未设置，则使用文件中的值

3. **Web 界面**（最低优先级）
   - 通过"系统设置"页面配置
   - 修改后保存到配置文件

## 📁 数据持久化

Railway 默认不提供持久化存储。如需保存生成的内容和历史记录：

### 方式一：使用 Railway Volume（推荐）

1. 在 Railway 项目中创建 Volume
2. 挂载到以下路径：
   - `/app/output` - 生成的图片
   - `/app/history` - 历史记录

### 方式二：使用云存储

修改代码，将图片上传到：
- AWS S3
- Google Cloud Storage
- Cloudflare R2

## 🔄 更新部署

### 自动部署

当您推送代码到 GitHub 的 `main` 分支时，Railway 会自动：
1. 拉取最新代码
2. 重新构建 Docker 镜像
3. 滚动更新服务（零停机）

### 手动部署

在 Railway Dashboard 中：
1. 点击 "Deployments" 标签
2. 点击最新的部署
3. 点击 "Redeploy"

## ❓ 常见问题

### Q: 提示 "API Key 未配置" 怎么办？

**A:** 检查以下几点：
1. 确认在 Railway 中添加了 `GOOGLE_API_KEY` 环境变量
2. 重新部署应用（修改环境变量后需要重启）
3. 查看部署日志，确认环境变量已正确加载

### Q: 如何查看日志？

**A:** 在 Railway Dashboard 中：
1. 点击您的服务
2. 点击 "Deployments" 标签
3. 选择最新的部署
4. 查看实时日志

### Q: 部署失败怎么办？

**A:** 常见原因：
1. Docker 构建失败：检查 Dockerfile 语法
2. 端口冲突：确保使用环境变量 `PORT`（Railway 自动提供）
3. 依赖安装失败：检查 `pyproject.toml` 和 `package.json`

查看详细错误信息：
```bash
# 在 Railway Dashboard 的 "Build Logs" 中查看构建日志
# 在 "Deploy Logs" 中查看运行时日志
```

### Q: 如何切换模型？

**A:** 两种方式：
1. **通过 Web 界面**：访问"系统设置"页面，编辑模型名称
2. **通过环境变量**：暂不支持，需要通过 Web 界面修改

### Q: 生成的图片保存在哪里？

**A:**
- 默认保存在容器的 `/app/output` 目录
- 容器重启后会丢失
- **建议**：配置 Railway Volume 或使用云存储

## 🌐 自定义域名

### 1. 在 Railway 中添加域名

1. 点击 "Settings" → "Domains"
2. 点击 "Custom Domain"
3. 输入您的域名（如 `glumoo.yourdomain.com`）

### 2. 在 Cloudflare 中配置 DNS

添加 CNAME 记录：
```
类型: CNAME
名称: glumoo
目标: your-app.up.railway.app
代理状态: 已代理（橙色云朵）
```

### 3. 更新 CORS 配置（可选）

如果您的前端部署在其他域名，需要在 Railway 中添加环境变量：

```bash
CORS_ORIGINS=https://app.yourdomain.com,https://glumoo.yourdomain.com
```

## 📊 监控和告警

Railway 提供基础监控：
- CPU 使用率
- 内存使用率
- 网络流量
- 请求日志

高级监控可使用：
- Sentry（错误追踪）
- Datadog（性能监控）
- LogRocket（用户行为）

## 💰 成本估算

Railway 定价（2026年）：
- **Hobby Plan**：免费额度 $5/月
- **Pro Plan**：$20/月起

Glumoo 应用预估成本：
- CPU: ~$5-10/月（取决于使用量）
- 内存: ~$2-5/月
- **总计**: 约 $10-15/月

> 💡 **节省成本技巧**：
> - 关闭高并发模式（减少 CPU 使用）
> - 使用 Railway 的 Sleep 功能（空闲时自动休眠）
> - 监控 API 调用次数（Google Gemini 有免费额度）

## 🔗 相关链接

- [Railway 官方文档](https://docs.railway.app)
- [Google Gemini API 文档](https://ai.google.dev/docs)
- [项目 GitHub](https://github.com/Yeadon8888/Glumoo_rednote)
- [问题反馈](https://github.com/Yeadon8888/Glumoo_rednote/issues)
