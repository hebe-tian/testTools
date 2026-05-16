# 部署指南

testTools 采用前后端分离部署方案：

- **前端**：Vercel（免费，自动 CI/CD）
- **后端**：PythonAnywhere（免费，支持 FastAPI）

---

## 方案一：Vercel (前端) + PythonAnywhere (后端) — 推荐

### 第一步：部署后端到 PythonAnywhere

#### 1. 注册 PythonAnywhere 账号

访问 https://www.pythonanywhere.com/ 注册免费账号。

#### 2. 创建 Web 应用

1. 登录后进入 **Dashboard**
2. 点击 **New app**
3. 选择域名：`<your-username>.pythonanywhere.com`
4. 选择 **Manual configuration** → **Python 3.11**

#### 3. 上传代码

方式 A：通过 Git 克隆（推荐）

```bash
# 在 PythonAnywhere 的 Bash Console 中执行
git clone https://github.com/<your-username>/testTools.git ~/testTools
```

方式 B：通过 Files 页面上传

#### 4. 配置虚拟环境

```bash
# 在 PythonAnywhere 的 Bash Console 中执行
cd ~/testTools/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 5. 配置 WSGI 文件

在 PythonAnywhere 的 **Web** 页面，点击 WSGI 配置链接，编辑 `/var/www/<your-username>_pythonanywhere_com_wsgi.py`：

```python
import os
import sys

# 添加项目路径
project_path = '/home/<your-username>/testTools/backend'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# 设置环境变量
os.environ['ALLOWED_ORIGINS'] = 'https://your-frontend.vercel.app'

# 导入 FastAPI 应用
from app.main import app

# PythonAnywhere 需要 asgi 应用
from fastapi.middleware.wsgi import WSGIMiddleware
application = WSGIMiddleware(app)
```

> **注意**：PythonAnywhere 免费版只支持 WSGI，不支持 ASGI。FastAPI 是 ASGI 框架，需要通过 `a2wsgi` 适配。安装方式：

```bash
pip install a2wsgi
```

然后修改 WSGI 文件：

```python
import os
import sys

project_path = '/home/<your-username>/testTools/backend'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

os.environ['ALLOWED_ORIGINS'] = 'https://your-frontend.vercel.app'

from app.main import app
from a2wsgi import ASGIMiddleware
application = ASGIMiddleware(app)
```

#### 6. 配置静态文件（可选）

在 Web 页面的 **Static files** 部分：

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/<your-username>/testTools/backend/static` |

#### 7. 重载应用

点击 Web 页面的 **Reload** 按钮。

#### 8. 验证

访问 `https://<your-username>.pythonanywhere.com/health`，应返回 `{"status": "ok"}`。

---

### 第二步：部署前端到 Vercel

#### 1. 安装 Vercel CLI

```bash
npm install -g vercel
```

#### 2. 创建 Vercel 配置文件

在项目根目录创建 `vercel.json`：

```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

#### 3. 配置环境变量

在 Vercel 项目设置中添加环境变量：

| 变量名 | 值 |
|--------|-----|
| `VITE_API_BASE_URL` | `https://<your-username>.pythonanywhere.com` |

或在 `frontend/` 目录创建 `.env.production`：

```
VITE_API_BASE_URL=https://<your-username>.pythonanywhere.com
```

#### 4. 部署

方式 A：通过 Vercel CLI

```bash
cd /path/to/testTools
vercel
```

方式 B：通过 GitHub 集成（推荐）

1. 将代码推送到 GitHub
2. 在 https://vercel.com 导入 GitHub 仓库
3. 配置：
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Environment Variables**: `VITE_API_BASE_URL` = `https://<your-username>.pythonanywhere.com`
4. 点击 Deploy

#### 5. 更新后端 CORS

部署前端后，在 PythonAnywhere 的 WSGI 配置中更新 `ALLOWED_ORIGINS` 为 Vercel 分配的域名，然后重载应用。

---

## 方案二：全部部署到 Vercel（Serverless）

Vercel 支持 Serverless Functions，可以用 Python 运行 FastAPI 后端。

#### 1. 安装 Vercel Python Runtime 依赖

在项目根目录创建 `api/index.py`：

```python
from backend.app.main import app

# Vercel Python Runtime 入口
handler = app
```

#### 2. 创建 vercel.json

```json
{
  "builds": [
    { "src": "frontend/package.json", "use": "@vercel/node" },
    { "src": "api/index.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "/api/index.py" },
    { "src": "/(.*)", "dest": "/frontend/$1" }
  ]
}
```

#### 3. 添加 requirements.txt 到项目根目录

```
fastapi>=0.100
uvicorn>=0.23
pydantic>=2.0
```

> **注意**：Vercel Serverless Functions 有 10 秒超时限制（免费版），且冷启动较慢。对于工具类应用足够使用。

---

## 方案三：全部部署到 PythonAnywhere

将前端构建为静态文件，由 PythonAnywhere 托管。

#### 1. 构建前端

```bash
cd frontend
VITE_API_BASE_URL=https://<your-username>.pythonanywhere.com npm run build
```

#### 2. 配置静态文件

在 PythonAnywhere Web 页面的 **Static files** 部分：

| URL | Directory |
|-----|-----------|
| `/` | `/home/<your-username>/testTools/frontend/dist` |
| `/assets/` | `/home/<your-username>/testTools/frontend/dist/assets` |

#### 3. 修改 WSGI 配置

让 FastAPI 只处理 `/api` 路径的请求，静态文件由 PythonAnywhere 的 Nginx 直接服务。

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

---

## 环境变量汇总

| 变量 | 位置 | 说明 | 示例 |
|------|------|------|------|
| `ALLOWED_ORIGINS` | 后端 | 允许的跨域来源，逗号分隔 | `https://testtools.vercel.app,http://localhost:5173` |
| `VITE_API_BASE_URL` | 前端（构建时） | 后端 API 地址 | `https://user.pythonanywhere.com` |
