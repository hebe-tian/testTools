# PythonAnywhere 部署指南

本文档详细说明如何将 testTools 后端部署到 PythonAnywhere 平台。

---

## 前置准备

### 1. 注册 PythonAnywhere 账号

访问 https://www.pythonanywhere.com/ 注册免费账号。

### 2. 准备代码仓库

将项目推送到 GitHub（或其他 Git 平台），方便在 PythonAnywhere 上克隆：

```bash
cd /path/to/testTools
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/<your-username>/testTools.git
git push -u origin main
```

---

## 部署步骤

### 第一步：创建 Web 应用

1. 登录 PythonAnywhere，进入 **Dashboard**
2. 点击 **Web** 标签页
3. 点击 **Add a new web app**
4. 选择域名：`<your-username>.pythonanywhere.com`（或自定义子域名）
5. 选择 **Manual configuration**
6. 选择 **Python 3.11**
7. 点击 **Next** 完成创建

### 第二步：上传代码

在 PythonAnywhere 的 **Bash Console** 中执行：

```bash
# 克隆项目
git clone https://github.com/<your-username>/testTools.git ~/testTools

# 或者如果已有代码，直接更新
cd ~/testTools
git pull origin main
```

### 第三步：配置虚拟环境

在 Bash Console 中执行：

```bash
# 进入后端目录
cd ~/testTools/backend

# 创建虚拟环境
python3.11 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# ⚠️ 重要：安装 ASGI 到 WSGI 适配器
pip install a2wsgi
```

### 第四步：配置环境变量

在 PythonAnywhere 的 **Web** 页面：

1. 找到 **Environment variables** 部分
2. 添加以下变量：

| Key | Value |
|-----|-------|
| `ALLOWED_ORIGINS` | `https://your-frontend-domain.com,http://localhost:5173` |

> **注意**：将 `https://your-frontend-domain.com` 替换为你实际的前端域名。如果有多个域名，用逗号分隔。

### 第五步：配置 WSGI 文件（关键步骤）

#### 1. 找到 WSGI 配置文件

在 **Web** 页面，点击 **WSGI configuration file** 链接，会打开编辑器。

文件路径通常是：`/var/www/<your-username>_pythonanywhere_com_wsgi.py`

#### 2. 编辑 WSGI 文件

**删除原有内容**，替换为以下代码：

```python
"""
PythonAnywhere WSGI 配置文件
用于将 FastAPI (ASGI) 应用转换为 WSGI 格式
"""
import os
import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== 配置项目路径 ====================
# 修改为你的实际用户名和项目路径
project_path = '/home/<your-username>/testTools/backend'

if project_path not in sys.path:
    sys.path.insert(0, project_path)
    logger.info(f"Project path added: {project_path}")

# ==================== 导入并转换应用 ====================
try:
    # 导入 FastAPI 应用实例
    from app.main import app
    logger.info("FastAPI app imported successfully")
    
    # 使用 a2wsgi 将 ASGI 应用转换为 WSGI
    # PythonAnywhere 只支持 WSGI，而 FastAPI 是 ASGI 框架
    from a2wsgi import ASGIMiddleware
    application = ASGIMiddleware(app)
    logger.info("ASGI to WSGI conversion completed")
    
except Exception as e:
    logger.error(f"Failed to initialize application: {str(e)}", exc_info=True)
    raise
```

#### 3. 修改占位符

将 `<your-username>` 替换为你的 PythonAnywhere 用户名。

例如，如果你的用户名是 `john123`，则路径应为：
```python
project_path = '/home/john123/testTools/backend'
```

#### 4. 保存文件

点击编辑器底部的 **Save** 按钮。

### 第六步：重载应用

在 **Web** 页面，点击绿色的 **Reload** 按钮。

等待几秒钟，应用就会重新加载。

### 第七步：验证部署

#### 1. 健康检查

访问：`https://<your-username>.pythonanywhere.com/health`

应该返回：
```json
{
  "status": "ok"
}
```

#### 2. API 文档

访问：`https://<your-username>.pythonanywhere.com/docs`

应该看到 FastAPI 的 Swagger UI 界面。

#### 3. 测试 API

访问：`https://<your-username>.pythonanywhere.com/api/v1/curl/docs`

或者直接测试解析接口：
```bash
curl -X POST "https://<your-username>.pythonanywhere.com/api/v1/curl/parse" \
  -H "Content-Type: application/json" \
  -d '{"curl_text": "curl https://api.example.com"}'
```

---

## 常见问题排查

### 问题 1：ImportError: No module named 'app'

**原因**：项目路径配置错误

**解决**：
1. 检查 WSGI 文件中的 `project_path` 是否正确
2. 确认路径指向包含 `app/` 目录的文件夹
3. 验证目录结构：
   ```bash
   ls -la /home/<your-username>/testTools/backend/app/
   # 应该能看到 main.py
   ```

### 问题 2：ModuleNotFoundError: No module named 'a2wsgi'

**原因**：未安装 a2wsgi 包

**解决**：
```bash
cd ~/testTools/backend
source venv/bin/activate
pip install a2wsgi
```

然后在 Web 页面点击 **Reload**。

### 问题 3：CORS 错误（跨域请求被阻止）

**原因**：`ALLOWED_ORIGINS` 环境变量未正确配置

**解决**：
1. 在 Web 页面的 **Environment variables** 部分检查设置
2. 确保包含你的前端域名
3. 多个域名用逗号分隔，不要有空格
4. 点击 **Reload** 使更改生效

### 问题 4：502 Bad Gateway

**原因**：应用启动失败

**解决**：
1. 查看错误日志：在 Web 页面点击 **Error log** 链接
2. 检查常见错误：
   - 导入错误
   - 依赖缺失
   - 路径配置错误
3. 修复后点击 **Reload**

### 问题 5：应用运行缓慢

**原因**：PythonAnywhere 免费版资源有限

**建议**：
- 优化代码性能
- 考虑升级到付费计划
- 使用缓存减少数据库查询

---

## 更新部署

当代码有更新时，按以下步骤操作：

### 方法 1：通过 Git 更新（推荐）

```bash
# 在 PythonAnywhere Bash Console 中执行
cd ~/testTools
git pull origin main

cd backend
source venv/bin/activate
pip install -r requirements.txt  # 如果依赖有变化
```

然后在 Web 页面点击 **Reload**。

### 方法 2：手动上传

1. 在本地重新打包代码
2. 通过 PythonAnywhere 的 **Files** 页面上传
3. 覆盖现有文件
4. 在 Web 页面点击 **Reload**

---

## 重要注意事项

### 1. PythonAnywhere 限制

- **免费版**：
  - 每天需要手动 Reload（或通过脚本自动）
  - CPU 和内存有限制
  - 只能访问白名单内的外部网站
  - 不支持 WebSocket
  
- **所有版本**：
  - 仅支持 WSGI，不支持原生 ASGI
  - 必须使用 `a2wsgi` 进行转换

### 2. 环境变量管理

**推荐做法**：
- ✅ 在 Web 页面的 Environment variables 部分设置
- ✅ 敏感信息（如密钥）不要硬编码在代码中

**不推荐**：
- ❌ 在 WSGI 文件中硬编码环境变量
- ❌ 在代码中写死配置

### 3. 日志查看

遇到问题时，查看以下日志：

- **Error log**：应用错误信息
- **Server log**：服务器访问日志
- **WSGI 文件中的 logger**：自定义日志输出

### 4. 静态文件

当前项目没有静态文件需求。如果需要提供静态文件：

在 Web 页面的 **Static files** 部分添加映射：

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/<your-username>/testTools/backend/static` |

---

## 技术说明

### 为什么需要 a2wsgi？

```
FastAPI (ASGI) → a2wsgi (转换器) → WSGI → PythonAnywhere
```

- **FastAPI** 是基于 ASGI（异步服务器网关接口）的现代框架
- **PythonAnywhere** 只支持传统的 WSGI（Web 服务器网关接口）
- **a2wsgi** 是一个桥接库，将 ASGI 应用转换为 WSGI 兼容格式

### 目录结构

```
/home/<your-username>/testTools/
└── backend/
    ├── app/
    │   ├── __init__.py
    │   ├── main.py          ← FastAPI 应用入口
    │   ├── api/
    │   ├── models/
    │   ├── services/
    │   └── utils/
    ├── venv/                ← 虚拟环境
    ├── requirements.txt
    └── tests/
```

### WSGI 文件工作流程

1. PythonAnywhere 加载 WSGI 文件
2. 设置 Python 路径，使其能找到项目模块
3. 导入 FastAPI 应用实例 (`app`)
4. 使用 `ASGIMiddleware` 包装应用
5. 导出 `application` 对象供 PythonAnywhere 使用

---

## 下一步

部署成功后，你可以：

1. **部署前端**：将前端部署到 Vercel、Netlify 等平台
2. **配置自定义域名**：在 PythonAnywhere 设置自定义域名
3. **监控应用**：定期检查日志和性能
4. **设置备份**：定期备份代码和数据

---

## 技术支持

如遇问题，可以：

1. 查看 PythonAnywhere 官方文档：https://help.pythonanywhere.com/
2. 查看 FastAPI 文档：https://fastapi.tiangolo.com/
3. 查看 a2wsgi 文档：https://github.com/abersheeran/a2wsgi
4. 检查项目 Issues 或提交新问题

---

**最后更新**：2026-05-19
