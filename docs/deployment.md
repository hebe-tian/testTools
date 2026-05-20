# 部署指南

testTools 采用前后端分离部署方案，支持多种平台组合。

---

## 目录

- [方案一：Vercel (前端) + PythonAnywhere (后端)](#方案一vercel-前端--pythonanywhere-后端)
- [方案二：全部部署到 Vercel (Serverless)](#方案二全部部署到-vercel-serverless)
- [方案三：全部部署到 PythonAnywhere](#方案三全部部署到-pythonanywhere)
- [方案四：Cloudflare 部署](#方案四cloudflare-部署)
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

#### 6. 重载应用

点击 **Web** 选项卡顶部绿色的 **Reload** 按钮。

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

## 方案二：全部部署到 Vercel (Serverless)

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

## 方案三：全部部署到 PythonAnywhere

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

## 方案四：Cloudflare 部署

Cloudflare 提供全球边缘网络，延迟低，免费额度充足。前端使用 Cloudflare Pages，后端使用 Cloudflare Workers，全部基于 GitHub 集成自动部署。

> 详细的操作步骤（包括每个按钮的位置、具体链接等）请参考 **[Cloudflare 部署指南](cloudflare-deployment.md)**。

简要流程：

1. **后端**：创建 `worker/` 目录和配置文件 → 在 Cloudflare Dashboard 导入 GitHub 仓库 → 推送代码自动部署到 Workers
2. **前端**：在 Cloudflare Pages 中连接 GitHub 仓库 → 推送代码自动构建部署
3. **配置 CORS**：Worker 代码中已内置跨域响应头

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

推送代码到 GitHub 即可自动部署，无需手动操作。

```bash
git add . && git commit -m "更新描述" && git push origin main
```
