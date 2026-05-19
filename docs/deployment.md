# 部署指南

testTools 采用前后端分离部署方案，支持多种平台组合。

---

## 目录

- [方案一：Vercel (前端) + PythonAnywhere (后端)](#方案一vercel-前端--pythonanywhere-后端)
- [方案二：Cloudflare Pages (前端) + Cloudflare Workers (后端)](#方案二cloudflare-pages-前端--cloudflare-workers-后端)
- [方案三：全部部署到 Vercel (Serverless)](#方案三全部部署到-vercel-serverless)
- [方案四：全部部署到 PythonAnywhere]((#方案四全部部署到-pythonanywhere)
- [环境变量汇总](#环境变量汇总)
- [更新部署](#更新部署)

---

## 方案一：Vercel (前端) + PythonAnywhere (后端)

### 第一步：部署后端到 PythonAnywhere

#### 1. 注册 PythonAnywhere 账号

访问 https://www.pythonanywhere.com/ 注册免费账号。

#### 2. 创建 Web 应用

1. 登录后进入 **Dashboard**
2. 点击 **Web** 选项卡 → **Add a new web app**
3. 确认域名：`<your-username>.pythonanywhere.com`
4. 选择 **Manual configuration** → **Python 3.11**（不要选 Django 等框架）

#### 3. 上传代码

在 PythonAnywhere 的 **Consoles** 选项卡中打开一个 **Bash console**：

```bash
git clone https://github.com/<your-username>/testTools.git ~/testTools
```

#### 4. 配置虚拟环境

```bash
cd ~/testTools/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install a2wsgi
```

> **为什么需要 a2wsgi？** PythonAnywhere 的 Web 应用只支持 WSGI 协议，而 FastAPI 是 ASGI 框架。`a2wsgi` 可以将 ASGI 应用转换为 WSGI 应用，让 FastAPI 在 PythonAnywhere 上正常运行。

#### 5. 配置 WSGI 文件

在 **Web** 选项卡中，点击 Code 部分的 WSGI 配置链接（路径类似 `/var/www/<your-username>_pythonanywhere_com_wsgi.py`），替换为：

```python
import os
import sys

project_path = '/home/<your-username>/testTools/backend'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

os.environ['ALLOWED_ORIGINS'] = 'https://your-frontend.vercel.app,http://localhost:5173'

from app.main import app
from a2wsgi import ASGIMiddleware
application = ASGIMiddleware(app)
```

> 将 `<your-username>` 替换为你的 PythonAnywhere 用户名。

#### 6. 配置 Virtualenv

在 **Web** 选项卡的 **Virtualenv** 部分，填入：

```
/home/<your-username>/testTools/backend/venv
```

#### 7. 重载应用

点击 **Web** 选项卡顶部绿色的 **Reload** 按钮。

#### 8. 验证后端可访问

在浏览器中访问以下 URL，确认后端正常运行：

| URL | 预期结果 |
|-----|---------|
| `https://<your-username>.pythonanywhere.com/health` | `{"status":"ok"}` |
| `https://<your-username>.pythonanywhere.com/docs` | FastAPI 自动文档页面 |
| `https://<your-username>.pythonanywhere.com/api/v1/curl/parse` | `{"detail":"Method Not Allowed"}`（正常，需要 POST） |

> **常见问题排查**：
> - 如果返回 502 错误：检查 WSGI 文件路径和虚拟环境路径是否正确
> - 如果返回 500 错误：在 Web 选项卡查看错误日志（Server log / Error log）
> - 如果修改了代码但没生效：必须点击 **Reload** 按钮重载应用

---

### 第二步：部署前端到 Vercel

#### 1. 通过 GitHub 集成部署（推荐）

1. 将代码推送到 GitHub
2. 访问 https://vercel.com 并用 GitHub 账号登录
3. 点击 **Add New** → **Project**
4. 选择 `testTools` 仓库
5. 配置：
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`（点击 Edit 输入）
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Environment Variables**:
     - `VITE_API_BASE_URL` = `https://<your-username>.pythonanywhere.com`
6. 点击 **Deploy**

#### 2. 更新后端 CORS

部署前端后，Vercel 会分配一个域名（如 `testtools-xxx.vercel.app`）。在 PythonAnywhere 的 WSGI 配置中更新 `ALLOWED_ORIGINS`：

```python
os.environ['ALLOWED_ORIGINS'] = 'https://testtools-xxx.vercel.app,http://localhost:5173'
```

然后点击 **Reload** 重载应用。

---

## 方案二：Cloudflare Pages (前端) + Cloudflare Workers (后端)

Cloudflare 提供全球边缘网络，延迟低，免费额度充足。

### 第一步：部署后端到 Cloudflare Workers

Cloudflare Workers 原生支持 Python，可以直接运行 FastAPI。

#### 1. 安装前置工具

```bash
# 安装 uv（Python 包管理器）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装 Node.js（需要 18+）
# 参见 https://nodejs.org/
```

#### 2. 创建 Workers 项目

在项目根目录创建 `worker/` 目录：

```bash
mkdir -p worker
cd worker
```

创建 `worker/pyproject.toml`：

```toml
[project]
name = "testtools-worker"
version = "0.1.0"
description = "testTools backend on Cloudflare Workers"
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

创建 `worker/src/entry.py`：

```python
from workers import WorkerEntrypoint, Response
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        url = str(request.url)

        if url.endswith("/health"):
            return Response(json.dumps({"status": "ok"}), headers={"Content-Type": "application/json"})

        if url.endswith("/api/v1/curl/parse") and request.method == "POST":
            body = await request.json()
            curl_text = body.get("curl_text", "")
            from app.services.curl_parser import parse
            try:
                result = parse(curl_text)
                return Response(result.model_dump_json(), headers={"Content-Type": "application/json"})
            except Exception as e:
                return Response(json.dumps({"detail": str(e)}), status=400, headers={"Content-Type": "application/json"})

        if url.endswith("/api/v1/curl/generate") and request.method == "POST":
            body = await request.json()
            from app.utils.curl_generator import generate
            from app.models.curl import CurlGenerateRequest
            try:
                req = CurlGenerateRequest(**body)
                result = generate(req)
                return Response(json.dumps({"curl_text": result, "shell_mode": req.shell_mode}), headers={"Content-Type": "application/json"})
            except Exception as e:
                return Response(json.dumps({"detail": str(e)}), status=400, headers={"Content-Type": "application/json"})

        return Response("Not Found", status=404)
```

创建 `worker/wrangler.toml`：

```toml
name = "testtools-backend"
main = "src/entry.py"
compatibility_flags = ["python_workers"]
compatibility_date = "2024-01-01"
```

#### 3. 本地测试

```bash
cd worker
uv run pywrangler dev
```

#### 4. 部署到 Cloudflare

```bash
uv run pywrangler deploy
```

部署成功后会输出 Worker URL，如 `https://testtools-backend.<your-subdomain>.workers.dev`。

> **注意**：Cloudflare Workers Python 仍处于 Beta 阶段。如果遇到兼容性问题，可以使用方案二（备选）：将后端部署为 Cloudflare Workers 的 JavaScript 版本，通过 `fetch` 调用外部 FastAPI 服务。

### 第二步：部署前端到 Cloudflare Pages

#### 1. 通过 GitHub 集成部署（推荐）

1. 登录 https://dash.cloudflare.com
2. 进入 **Workers & Pages** → **Create** → **Pages** → **Connect to Git**
3. 选择 `testTools` 仓库
4. 配置：
   - **Production branch**: `main`
   - **Build command**: `cd frontend && npm install && npm run build`
   - **Build output directory**: `frontend/dist`
   - **Environment variables**:
     - `VITE_API_BASE_URL` = `https://testtools-backend.<your-subdomain>.workers.dev`
5. 点击 **Save and Deploy**

#### 2. 通过 CLI 部署

```bash
cd frontend
npm run build
npx wrangler pages deploy dist --project-name=testtools
```

#### 3. 更新后端 CORS

在 Cloudflare Workers 的 `wrangler.toml` 中添加环境变量，或在 Cloudflare Dashboard 的 Workers 设置中添加：

```
ALLOWED_ORIGINS=https://testtools.pages.dev
```

---

## 方案三：全部部署到 Vercel (Serverless)

Vercel 支持 Serverless Functions，可以用 Python 运行 FastAPI 后端。

#### 1. 在项目根目录创建 `api/index.py`

```python
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

os.environ.setdefault('ALLOWED_ORIGINS', '*')

from app.main import app
handler = app
```

#### 2. 在项目根目录创建 `requirements.txt`

```
fastapi>=0.100
pydantic>=2.0
```

#### 3. 创建 `vercel.json`

```json
{
  "builds": [
    { "src": "api/index.py", "use": "@vercel/python" },
    { "src": "frontend/package.json", "use": "@vercel/node" }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "/api/index.py" },
    { "src": "/health", "dest": "/api/index.py" },
    { "src": "/docs", "dest": "/api/index.py" },
    { "src": "/openapi.json", "dest": "/api/index.py" },
    { "src": "/(.*)", "dest": "/frontend/$1" }
  ]
}
```

#### 4. 部署

```bash
vercel --prod
```

> **注意**：Vercel Serverless Functions 免费版有 10 秒超时限制，且冷启动较慢。对于工具类应用足够使用。

---

## 方案四：全部部署到 PythonAnywhere

将前端构建为静态文件，由 PythonAnywhere 托管。

#### 1. 构建前端

```bash
cd frontend
VITE_API_BASE_URL=https://<your-username>.pythonanywhere.com npm run build
```

#### 2. 配置静态文件映射

在 PythonAnywhere **Web** 选项卡的 **Static files** 部分：

| URL | Directory |
|-----|-----------|
| `/assets/` | `/home/<your-username>/testTools/frontend/dist/assets` |

#### 3. 修改 WSGI 配置

在 WSGI 文件中添加静态文件服务逻辑，让 `/api` 路径走 FastAPI，其他路径返回 `index.html`：

```python
import os
import sys

project_path = '/home/<your-username>/testTools/backend'
dist_path = '/home/<your-username>/testTools/frontend/dist'

if project_path not in sys.path:
    sys.path.insert(0, project_path)

os.environ['ALLOWED_ORIGINS'] = 'https://<your-username>.pythonanywhere.com'

from a2wsgi import ASGIMiddleware
from app.main import app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.mount("/assets", StaticFiles(directory=os.path.join(dist_path, "assets")), name="assets")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    file_path = os.path.join(dist_path, full_path)
    if full_path and os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(dist_path, "index.html"))

application = ASGIMiddleware(app)
```

#### 4. 访问应用

直接访问 `https://<your-username>.pythonanywhere.com` 即可看到首页。

---

## 环境变量汇总

| 变量 | 位置 | 说明 | 示例 |
|------|------|------|------|
| `ALLOWED_ORIGINS` | 后端 | 允许的跨域来源，逗号分隔 | `https://testtools.vercel.app,http://localhost:5173` |
| `VITE_API_BASE_URL` | 前端（构建时） | 后端 API 地址 | `https://user.pythonanywhere.com` |

---

## 更新部署

### PythonAnywhere 更新

```bash
cd ~/testTools
git pull origin main
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

然后在 Web 页面点击 **Reload**。

### Vercel 更新

如果通过 GitHub 集成，推送代码后自动部署。否则：

```bash
vercel --prod
```

### Cloudflare 更新

```bash
# 前端（Pages 自动部署，或手动）
cd frontend && npm run build && npx wrangler pages deploy dist --project-name=testtools

# 后端（Workers）
cd worker && uv run pywrangler deploy
```
