# Railway 部署问题修复说明

## 🔧 已修复的问题

### 1. ✅ Flask 开发服务器警告
**问题**: 在生产环境使用 Flask 开发服务器
```
WARNING: This is a development server. Do not use it in a production deployment.
```

**解决方案**: 
- 添加 `gunicorn` 作为生产级 WSGI 服务器
- 配置：2 个 worker 进程，每个 4 个线程
- 超时时间：120 秒（适应 AI 生成的长时间请求）

### 2. ✅ uv 配置弃用警告
**问题**: 
```
warning: The `tool.uv.dev-dependencies` field is deprecated
```

**解决方案**: 
更新 `pyproject.toml`，使用新格式：
```toml
[dependency-groups]
dev = []
```

### 3. ✅ Railway 端口配置
**问题**: 使用硬编码端口 `12398`，Railway 无法正确路由请求

**解决方案**: 
- 代码优先读取 `PORT` 环境变量（Railway 自动提供）
- 本地开发回退到 `12398`
- gunicorn 绑定到 `0.0.0.0:${PORT:-12398}`

### 4. ✅ 调试模式配置
**问题**: 生产环境启用了调试模式 (`DEBUG=True`)

**解决方案**: 
- 通过环境变量控制：`FLASK_DEBUG`
- Dockerfile 默认设置为 `False`
- 支持在 Railway 中按需启用

## 📋 部署检查清单

### Railway 环境变量

确保在 Railway Dashboard 中配置以下环境变量：

| 变量名 | 必填 | 说明 | 示例 |
|--------|------|------|------|
| `GOOGLE_API_KEY` | ✅ | Google Gemini API Key | `AIzaSy...` |
| `FLASK_DEBUG` | ❌ | 调试模式（默认 False） | `False` |

> ⚠️ **重要**: Railway 会自动提供 `PORT` 环境变量，无需手动配置！

### 部署步骤

1. **提交代码到 Git**
   ```bash
   git add .
   git commit -m "fix: 修复 Railway 部署问题"
   git push origin main
   ```

2. **Railway 自动部署**
   - Railway 检测到代码变更
   - 重新构建 Docker 镜像（约 3-5 分钟）
   - 自动部署新版本

3. **验证部署**
   访问以下端点确认服务正常：
   - 健康检查: `https://your-app.railway.app/api/health`
   - API 信息: `https://your-app.railway.app/`

## 📊 预期日志

部署成功后，日志应显示：

```
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/...
Starting Container
Building glumoo-pet-agent @ file:///app
Installed X packages in XXms
[YYYY-MM-DD HH:MM:SS] INFO - 🚀 正在启动 Glumoo 小红书宠物图文Agent...
[YYYY-MM-DD HH:MM:SS] INFO - 📦 检测到前端构建产物，启用静态文件托管模式
[YYYY-MM-DD HH:MM:SS] INFO - 📋 检查配置文件...
[YYYY-MM-DD HH:MM:SS] INFO - ✅ 文本生成配置: 激活=gemini, 可用服务商=['gemini']
[YYYY-MM-DD HH:MM:SS] INFO - ✅ 文本服务商 [gemini] API Key 已配置（来自环境变量）
[YYYY-MM-DD HH:MM:SS] INFO - ✅ 图片生成配置: 激活=gemini, 可用服务商=['gemini']
[YYYY-MM-DD HH:MM:SS] INFO - ✅ 图片服务商 [gemini] API Key 已配置（来自环境变量）
[YYYY-MM-DD HH:MM:SS] INFO - ✅ 配置检查完成
[YYYY-MM-DD HH:MM:SS +0000] [1] [INFO] Starting gunicorn 21.2.0
[YYYY-MM-DD HH:MM:SS +0000] [1] [INFO] Listening at: http://0.0.0.0:XXXX
[YYYY-MM-DD HH:MM:SS +0000] [1] [INFO] Using worker: sync
[YYYY-MM-DD HH:MM:SS +0000] [X] [INFO] Booting worker with pid: X
[YYYY-MM-DD HH:MM:SS +0000] [X] [INFO] Booting worker with pid: X
```

**关键变化**:
- ❌ 不再出现 "This is a development server" 警告
- ✅ 显示 "Starting gunicorn" 表示使用生产服务器
- ✅ 显示正确的端口（Railway 分配的端口，通常是随机的）
- ❌ 不再出现 uv dev-dependencies 警告

## 🔍 故障排查

### 问题 1: 仍然看到开发服务器警告

**可能原因**: 
- Dockerfile 构建缓存未更新
- railway.toml 的 startCommand 覆盖了 Dockerfile CMD

**解决方案**:
```bash
# 在 Railway Dashboard 中触发完整重建
# Settings > Deployments > 最新部署 > Redeploy
```

### 问题 2: 应用启动失败

**检查日志**:
1. Railway Dashboard > Deployments > View Logs
2. 查看 "Build Logs" 和 "Deploy Logs"

**常见错误**:
- `ModuleNotFoundError`: 依赖未正确安装 → 检查 `pyproject.toml`
- `Port already in use`: 端口冲突 → 确认使用 `$PORT` 环境变量
- `API Key not found`: 环境变量未配置 → 检查 Railway Variables

### 问题 3: gunicorn 超时

如果 AI 生成请求超过 120 秒，修改 Dockerfile:

```dockerfile
CMD uv run gunicorn --bind 0.0.0.0:${PORT:-12398} \
    --workers 2 --threads 4 --timeout 300 \  # 增加到 300 秒
    --access-logfile - --error-logfile - "backend.app:create_app()"
```

## 🚀 性能优化建议

### Worker 配置

当前配置：2 workers × 4 threads = 8 并发请求

**调整建议**:
- **低流量** (< 10 QPS): `--workers 1 --threads 2`
- **中流量** (10-50 QPS): `--workers 2 --threads 4` ✅ 当前配置
- **高流量** (> 50 QPS): `--workers 4 --threads 4`

修改 Dockerfile 的 CMD 行即可。

### Railway Resources

在 Railway Dashboard 中调整资源：
- Settings > Resources
- 推荐：512MB 内存起步
- CPU: 根据实际负载调整

## 📚 相关文档

- [Flask 部署选项](https://flask.palletsprojects.com/en/latest/deploying/)
- [Gunicorn 配置](https://docs.gunicorn.org/en/stable/settings.html)
- [Railway 文档](https://docs.railway.app/)
- [uv 文档](https://docs.astral.sh/uv/)

## 🎯 下一步

1. ✅ 修复已完成，准备部署
2. 📤 提交代码到 GitHub
3. 🚀 等待 Railway 自动部署
4. ✅ 验证部署成功
5. 🌐 （可选）配置自定义域名

---

**最后更新**: 2026-01-07
**状态**: ✅ 已修复所有已知问题
