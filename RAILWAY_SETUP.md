# Railway 部署配置指南

## 问题：历史记录在重新部署后丢失

### 原因
Railway 每次重新部署都会创建全新的容器，容器内的文件系统是临时的。`history/` 和 `output/` 目录中的数据会在重新部署时丢失。

### 解决方案：配置持久化卷（Volumes）

## 🔧 配置步骤

### 1. 登录 Railway Dashboard
访问 https://railway.app/dashboard，进入你的项目。

### 2. 选择服务
点击你的 Glumoo 部署服务（通常是从 GitHub 自动部署的服务）。

### 3. 添加 Volume 1 - 历史记录

1. 点击 **Settings** 标签
2. 滚动到 **Volumes** 部分
3. 点击 **+ New Volume** 按钮
4. 填写以下信息：
   - **Mount Path**: `/app/history`
   - **Volume Name**: `glumoo-history`（可自定义）
5. 点击 **Add** 保存

### 4. 添加 Volume 2 - 生成的图片

重复上述步骤，添加第二个卷：
- **Mount Path**: `/app/output`
- **Volume Name**: `glumoo-output`（可自定义）

### 5. 重新部署

配置完成后，Railway 会自动触发重新部署。等待部署完成。

### 6. 验证配置

部署成功后：
1. 访问你的应用
2. 生成一些内容和历史记录
3. 在 Railway Dashboard 中手动触发重新部署（Settings > Deploy）
4. 部署完成后，检查历史记录是否还在

## 📊 Volume 配置说明

| 目录 | 用途 | Volume 挂载路径 | 建议大小 |
|------|------|----------------|---------|
| `/app/history` | 历史记录（JSON 文件） | `/app/history` | 1GB |
| `/app/output` | 生成的图片文件 | `/app/output` | 5GB |

## ⚠️ 重要提示

1. **首次配置后会重新部署**：添加 Volume 后，Railway 会自动重新部署，之前的数据会丢失。这是正常的，之后的数据就会持久化保存。

2. **Volume 独立于部署**：即使删除部署或重新部署，Volume 中的数据会保留。

3. **删除 Volume 前备份**：如果需要删除 Volume，请先备份数据。删除 Volume 会永久删除其中的数据。

4. **Volume 计费**：Railway 的 Volume 存储会计入使用量，请注意定期清理不需要的历史记录和图片。

## 🔍 排查问题

### 如何查看 Volume 是否生效？

在 Railway Dashboard 的服务页面：
1. 点击 **Deployments** 标签
2. 选择最新的部署
3. 点击 **Logs** 查看日志
4. 搜索 "history" 或 "output"，确认应用能正常访问这些目录

### 如何手动备份数据？

你可以通过 Railway CLI 连接到容器并下载数据：

```bash
# 安装 Railway CLI
npm install -g @railway/cli

# 登录
railway login

# 连接到项目
railway link

# 进入容器 shell
railway run bash

# 在容器内查看数据
ls -la /app/history
ls -la /app/output

# 退出容器
exit
```

然后通过 SFTP 或其他方式下载文件。

## 📚 相关文档

- [Railway Volumes 官方文档](https://docs.railway.app/reference/volumes)
- [Railway CLI 文档](https://docs.railway.app/develop/cli)

## 🆘 还有问题？

如果配置后仍有问题：
1. 检查 Railway 日志，确认没有权限错误
2. 确认 Dockerfile 中创建了 `history` 和 `output` 目录
3. 联系 Railway 支持
