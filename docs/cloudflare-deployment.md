# Cloudflare 部署指南

本文档详细介绍如何将 testTools 应用部署到 Cloudflare 平台。**全部操作在 Cloudflare Dashboard 上完成**——通过绑定 GitHub 仓库，Cloudflare 会自动拉取代码、构建并部署，推送代码后自动更新。

---

## 目录

- [部署方案概览](#部署方案概览)
- [前置准备](#前置准备)
- [第一步：创建 Worker 项目文件并推送到 GitHub](#第一步创建-worker-项目文件并推送到-github)
- [第二步：在 Cloudflare 上导入后端 Worker](#第二步在-cloudflare-上导入后端-worker)
- [第三步：在 Cloudflare 上部署前端 Pages](#第三步在-cloudflare-上部署前端-pages)
- [验证部署结果](#验证部署结果)
- [日常更新流程](#日常更新流程)
- [常见问题排查](#常见问题排查)

---

## 部署方案概览

| 组件 | Cloudflare 服务 | 部署方式 | 自动触发 |
|------|----------------|----------|----------|
| 后端 API | Cloudflare Workers | Dashboard 导入 GitHub 仓库 | 推送到 `main` 分支自动部署 |
| 前端页面 | Cloudflare Pages | Dashboard 连接 GitHub 仓库 | 推送到 `main` 分支自动构建 |

**工作流程**：

```
你推送代码到 GitHub
        │
        ├──→ Cloudflare Workers 自动检测
        │         │
        │         └──→ 拉取 worker/ 目录 → 安装依赖 → 部署 → 后端更新完成
        │
        └──→ Cloudflare Pages 自动检测
                  │
                  └──→ 拉取仓库 → npm install → npm run build → 前端更新完成
```

---

## 前置准备

在开始之前，请确认你已经完成以下准备工作：

| 准备项 | 说明 | 检查方法 |
|--------|------|----------|
| GitHub 仓库 | 代码已推送到 GitHub | 访问 `https://github.com/<你的用户名>/testTools` |
| Cloudflare 账号 | 已注册 Cloudflare 账号 | 访问 **https://dash.cloudflare.com** 能正常登录 |

### 注册 Cloudflare 账号（如还没有）

1. 打开浏览器，访问 **https://dash.cloudflare.com/sign-up**
2. 输入邮箱地址和密码
3. 完成邮箱验证
4. 登录成功后进入 Dashboard 控制台首页

---

## 第一步：创建 Worker 项目文件并推送到 GitHub

Cloudflare Workers 需要项目中有配置文件才能正确构建。这些文件需要提交到 GitHub 仓库中。

### 1. 创建目录结构

```bash
cd /Users/linleil/Desktop/testTools
mkdir -p worker/src
```

最终结构如下：

```
testTools/
├── backend/              # 后端源码
├── frontend/             # 前端源码
├── worker/               # Cloudflare Workers 项目（新建）
│   ├── src/
│   │   └── entry.py      # Worker 入口文件
│   ├── pyproject.toml     # Python 依赖配置
│   └── wrangler.toml      # Cloudflare Worker 配置
└── docs/
```

### 2. 创建 `worker/pyproject.toml`

这个文件定义了 Worker 的 Python 依赖包：

```toml
[project]
name = "testtools-backend"
version = "0.1.0"
description = "testTools backend API on Cloudflare Workers"
requires-python = ">=3.12"
dependencies = [
    "fastapi",
    "pydantic",
]

[dependency-groups]
dev = [
    "workers-py",
    "workers-runtime-sdk",
]
```

### 3. 创建 `worker/src/entry.py`

这是 Worker 的入口文件，负责处理所有 HTTP 请求。代码中已内置 CORS 处理：

```python
"""Cloudflare Worker 入口文件 - 处理 testTools 后端 API 请求"""

import json
from workers import WorkerEntrypoint, Response


class Default(WorkerEntrypoint):
    """默认的 Worker 入口类，处理所有 HTTP 请求"""

    async def fetch(self, request):
        """处理所有入站请求的路由分发"""
        url = str(request.url)
        method = request.method

        cors_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }

        if method == "OPTIONS":
            return Response("", status=204, headers=cors_headers)

        if url.endswith("/health"):
            return Response(
                json.dumps({"status": "ok"}),
                headers={"Content-Type": "application/json", **cors_headers}
            )

        if url.endswith("/api/v1/curl/parse") and method == "POST":
            resp = await self._handle_parse(request)
            return resp

        if url.endswith("/api/v1/curl/generate") and method == "POST":
            resp = await self._handle_generate(request)
            return resp

        return Response("Not Found", status=404, headers=cors_headers)

    async def _handle_parse(self, request):
        """处理 curl 解析请求"""
        cors_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
        try:
            body = await request.json()
            curl_text = body.get("curl_text", "")

            from app.services.curl_parser import parse
            result = parse(curl_text)

            return Response(
                result.model_dump_json(),
                headers={"Content-Type": "application/json", **cors_headers}
            )
        except Exception as e:
            return Response(
                json.dumps({"detail": str(e)}),
                status=400,
                headers={"Content-Type": "application/json", **cors_headers}
            )

    async def _handle_generate(self, request):
        """处理 curl 生成请求"""
        cors_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
        try:
            body = await request.json()

            from app.utils.curl_generator import generate
            from app.models.curl import CurlGenerateRequest

            req = CurlGenerateRequest(**body)
            result = generate(req)

            return Response(
                json.dumps({"curl_text": result, "shell_mode": req.shell_mode}),
                headers={"Content-Type": "application/json", **cors_headers}
            )
        except Exception as e:
            return Response(
                json.dumps({"detail": str(e)}),
                status=400,
                headers={"Content-Type": "application/json", **cors_headers}
            )
```

### 4. 创建 `worker/wrangler.toml`

这个文件是 Cloudflare Worker 的配置文件：

```toml
name = "testtools-backend"
main = "src/entry.py"
compatibility_flags = ["python_workers"]
compatibility_date = "2024-01-01"
```

> `python_workers` 兼容性标志是必须的，它告诉 Cloudflare 这是一个 Python Worker。

### 5. 提交到 GitHub

```bash
cd /Users/linleil/Desktop/testTools
git add worker/
git commit -m "添加 Cloudflare Worker 项目文件"
git push origin main
```

---

## 第二步：在 Cloudflare 上导入后端 Worker

在 Cloudflare Dashboard 上直接绑定 GitHub 仓库来部署后端 Worker。

### 1. 进入 Workers & Pages 页面

1. 打开浏览器，访问 **https://dash.cloudflare.com**
2. 确保你已经登录了 Cloudflare 账号
3. 在左侧菜单栏找到并点击 **"Workers & Pages"**

### 2. 创建新的 Worker 项目

1. 在 **Workers & Pages** 页面，点击右上角的 **"Create"** 按钮

2. 在弹出的页面中，你会看到两个区域：**"Create Worker"** 和 **"Import a repository"**

3. 在 **"Import a repository"** 区域，点击 **"Get started"** 按钮

   > 如果是首次使用，会跳转到 GitHub 授权页面

### 3. 授权 GitHub 访问

1. 在 GitHub 授权页面，你可以选择授权范围：
   - **"All repositories"**：授权访问所有仓库
   - **"Only select repositories"**：仅授权访问指定仓库（推荐）

2. 如果选择 **"Only select repositories"**：
   - 在 **"Repositories"** 下拉列表中选择 **testTools** 仓库
   - 点击绿色的 **"Install & Authorize"** 按钮

3. 授权成功后自动回到 Cloudflare 页面

### 4. 选择仓库

1. 回到 Cloudflare 后，在 **"Git account"** 下拉框中选择你的 GitHub 账号
2. 在下方的仓库列表中找到并点击 **testTools** 仓库
3. 点击 **"Begin setup"** 按钮

### 5. 配置构建设置

在配置页面，填写以下信息：

| 配置项 | 填写内容 | 说明 |
|--------|----------|------|
| Project name | `testtools-backend` | 必须与 `wrangler.toml` 中的 `name` 一致 |
| Production branch | `main` | |
| Root Directory | `worker` | 点击 **"Edit"** 输入，告诉 Cloudflare Worker 代码在 `worker/` 子目录 |
| Build command | 留空 | Python Worker 不需要构建步骤 |
| Deploy command | `uv run pywrangler deploy` | 使用 pywrangler 部署 Python Worker |

> **Root Directory 很重要**：因为我们的项目是 monorepo（前端、后端、Worker 在同一仓库的不同目录），必须设置 Root Directory 为 `worker`，这样 Cloudflare 才会在正确的目录下查找 `wrangler.toml`。

> **Project name 必须匹配**：Cloudflare 要求 Dashboard 中的项目名与 `wrangler.toml` 中的 `name` 字段一致，否则构建会失败。

### 6. 配置构建监控路径（可选但推荐）

为了避免前端代码变更触发后端重新部署，建议配置 Build watch paths：

1. 在同一个配置页面，找到 **"Build watch paths"** 部分
2. 在 **"Include paths"** 中填入：`worker/*, backend/*`
3. 这样只有 `worker/` 或 `backend/` 目录下的文件变更才会触发后端部署

### 7. 保存并部署

1. 点击页面底部的 **"Save and Deploy"** 按钮
2. Cloudflare 会立即开始拉取代码并部署
3. 部署过程大约需要 1~2 分钟
4. 部署成功后，页面会显示 **"Success"** 绿色提示

### 8. 查看 Worker URL

1. 部署成功后，在 Worker 项目页面可以看到访问地址
2. 格式为：**`https://testtools-backend.<你的子域>.workers.dev`**
3. **记住这个 URL**，第三步配置前端时需要用到

---

## 第三步：在 Cloudflare 上部署前端 Pages

通过 Cloudflare Pages 的 GitHub 集成，绑定同一个 GitHub 仓库来部署前端。

### 1. 进入创建页面

1. 在 **Workers & Pages** 页面，点击右上角的 **"Create"** 按钮
2. 在弹出的页面中选择 **"Pages"** 标签页
3. 点击 **"Connect to Git"** 按钮

### 2. 选择仓库

1. 在 **"Git account"** 下拉框中选择你的 GitHub 账号（第二步已授权过，无需再次授权）
2. 在仓库列表中找到并点击 **testTools** 仓库

### 3. 配置构建设置

在配置页面，填写以下信息：

| 配置项 | 填写内容 | 说明 |
|--------|----------|------|
| Project name | `testtools` | 或任意你喜欢的名字 |
| Production branch | `main` | |
| Build command | `cd frontend && npm install && npm run build` | 先进入前端目录再构建 |
| Build output directory | `frontend/dist` | 构建产物的位置 |

> **Build command 说明**：因为项目根目录不是 frontend，所以需要先 `cd frontend` 进入前端目录再执行构建。

### 4. 配置环境变量

在同一个配置页面向下滚动，找到 **"Environment variables"** 部分：

1. 点击 **"Add variable"** 按钮
2. 添加以下变量：

   | 变量名 | 变量值 |
   |--------|--------|
   | `VITE_API_BASE_URL` | `https://testtools-backend.<你的子域>.workers.dev` |

   > 把 `<你的子域>` 替换为第二步中获得的实际子域名。

3. 添加完成后继续

### 5. 保存并部署

1. 点击页面底部的 **"Save and Deploy"** 按钮
2. Cloudflare 会立即开始构建，这个过程大约需要 1~3 分钟
3. 构建进度会实时显示在页面上
4. 构建完成后，页面会显示 **"Success"** 绿色提示
5. 你会得到一个 Pages URL，格式为：**`https://testtools.pages.dev`**

---

## 验证部署结果

### 验证后端

在浏览器中访问以下 URL：

| 测试项 | URL | 预期结果 |
|--------|-----|---------|
| 健康检查 | `https://testtools-backend.<子域>.workers.dev/health` | `{"status":"ok"}` |

### 验证前端

1. 在浏览器中访问 `https://testtools.pages.dev`
2. 应该能看到 testTools 首页，展示工具列表
3. 点击 **"curl 编解码器"** 进入工具页面
4. 输入一条 curl 命令（如 `curl https://example.com`），点击 **"解析"**
5. 确认解析结果正常显示

---

## 日常更新流程

部署完成后，日常更新非常简单——**只需要推送代码到 GitHub**，Cloudflare 会自动检测变更并重新部署。

### 更新后端代码

```bash
# 修改 backend/ 或 worker/ 下的代码后
git add .
git commit -m "描述你的修改"
git push origin main
```

推送后，Cloudflare Workers 会自动检测到 `worker/` 或 `backend/` 目录的变更并重新部署。

### 更新前端代码

```bash
# 修改 frontend/ 下的代码后
git add .
git commit -m "描述你的修改"
git push origin main
```

推送后，Cloudflare Pages 会自动检测到变更并重新构建前端。

### 查看部署状态

**后端部署状态**：

1. 访问 **https://dash.cloudflare.com**
2. 左侧菜单 → **"Workers & Pages"**
3. 点击 **"testtools-backend"**
4. 点击 **"Deployments"** 标签查看所有部署记录

**前端部署状态**：

1. 访问 **https://dash.cloudflare.com**
2. 左侧菜单 → **"Workers & Pages"**
3. 点击 **"testtools"**
4. 点击 **"Deployments"** 标签查看所有构建记录

### 回滚到之前的版本

1. 在 Cloudflare Dashboard 中进入对应项目（Worker 或 Pages）
2. 点击 **"Deployments"** 标签
3. 找到之前正常工作的版本，点击右侧的 **"..."** 按钮
4. 选择 **"Rollback to this deployment"**

---

## 常见问题排查

### 问题 1：Worker 构建失败，提示 "name mismatch"

**原因**：Dashboard 中的项目名与 `wrangler.toml` 中的 `name` 不一致

**解决**：

1. 打开 `worker/wrangler.toml`，确认 `name = "testtools-backend"`
2. 在 Cloudflare Dashboard 中确认项目名也是 `testtools-backend`
3. 两者必须完全一致

### 问题 2：Worker 构建失败，提示找不到 `wrangler.toml`

**原因**：Root Directory 没有设置为 `worker`

**解决**：

1. 在 Cloudflare Dashboard 中进入 Worker 项目
2. 点击 **"Settings"** → **"Builds"**
3. 将 **"Root Directory"** 修改为 `worker`
4. 点击 **"Save"**，然后重新触发部署

### 问题 3：前端能打开但 API 调用失败（CORS 错误）

**原因**：浏览器阻止了跨域请求

**解决**：
- 检查 `worker/src/entry.py` 中的 `cors_headers` 是否正确
- 检查前端的 `VITE_API_BASE_URL` 是否指向正确的 Worker URL
- 打开浏览器开发者工具（F12）→ **"Network"** 标签查看具体错误信息

### 问题 4：Pages 构建失败

**原因**：通常是 npm 依赖安装问题或构建路径不对

**解决**：

1. 在 Cloudflare Dashboard 中进入 Pages 项目
2. 点击 **"Deployments"** 标签
3. 点击最近一次失败的部署
4. 查看构建日志了解具体错误原因
5. 常见修复：
   - 确保 Build command 为 `cd frontend && npm install && npm run build`
   - 确保 Build output directory 为 `frontend/dist`
   - 检查 `frontend/package.json` 是否存在

### 问题 5：Worker 返回 500 内部错误

**原因**：代码运行时出错

**解决**：

1. 在 Cloudflare Dashboard 中进入 Worker 项目
2. 点击 **"Logs"** 标签（或 **"Logs & Metrics"**）
3. 点击 **"Begin log stream"** 按钮
4. 再次触发请求，查看具体的错误堆栈信息

### 问题 6：GitHub 仓库列表中看不到 testTools

**原因**：授权时没有选择该仓库

**解决**：

1. 访问 **https://github.com/settings/installations**
2. 找到 **"Cloudflare Workers and Pages"**，点击 **"Configure"**
3. 在 **"Repository access"** 中选择 **"Only select repositories"**
4. 在下拉列表中添加 **testTools** 仓库
5. 点击 **"Save"**
6. 回到 Cloudflare Dashboard 刷新页面

### 问题 7：免费额度限制

Cloudflare 免费计划的限制：

| 资源 | 免费额度 | 对本项目的影响 |
|------|----------|---------------|
| Workers 请求次数 | 100,000 次/天 | 个人使用完全够用 |
| Workers CPU 时间 | 10ms/请求 | API 请求足够快 |
| Pages 请求数 | 无限 | 前端无限制 |
| Pages 构建次数 | 500 次/月 | 正常开发够用 |

---

## 附录：快速参考卡

### 你的部署地址汇总

| 服务 | 地址格式 | 示例 |
|------|----------|------|
| 后端 API | `https://<name>.<subdomain>.workers.dev` | `https://testtools-backend.abc123.workers.dev` |
| 前端页面 | `https://<name>.pages.dev` | `https://testtools.pages.dev` |
| Cloudflare Dashboard | `https://dash.cloudflare.com` | - |

### 关键配置页面直达链接

| 页面 | 链接 |
|------|------|
| Cloudflare Dashboard | https://dash.cloudflare.com |
| Workers & Pages | https://dash.cloudflare.com → 左侧菜单 "Workers & Pages" |
| GitHub 授权管理 | https://github.com/settings/installations |
| API 令牌管理 | https://dash.cloudflare.com/profile/api-tokens |

### 日常更新命令

```bash
# 修改代码后，只需一条命令
git add . && git commit -m "更新描述" && git push origin main
# 后端和前端都会自动部署
```
