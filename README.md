# testTools

测试工具集 Web 应用，提供多种开发测试工具。首个工具为 **Curl Coder** — curl 命令解析与生成器。

## 功能

- **Curl Coder**：解析 curl 命令为结构化信息（HTTP 方法、URL、请求头、请求体、认证等），支持编辑后重新生成 curl 命令
  - 支持 bash/zsh、PowerShell、CMD 三种 shell 格式自动检测
  - 支持美化/紧凑两种输出模式
  - 可编辑所有字段并重新生成

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | FastAPI + Pydantic v2 + Uvicorn |
| 前端 | React 19 + TypeScript + Vite 8 |
| 测试 | pytest + httpx (后端) |
| 代码质量 | ruff + mypy (后端) + ESLint (前端) |

## 本地开发

### 前置要求

- Python 3.11+
- Node.js 22+

### 1. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

后端运行在 http://localhost:8000，API 文档在 http://localhost:8000/docs

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 http://localhost:5173，已配置 proxy 将 `/api` 请求转发到后端。

### 3. 运行测试

```bash
# 后端测试
cd backend
pytest -v

# 带覆盖率
pytest --cov=app --cov-report=term-missing
```

### 4. 代码质量检查

```bash
# 后端
cd backend
python3 -m ruff check .
python3 -m mypy app/ --ignore-missing-imports

# 前端
cd frontend
npx tsc --noEmit
npx eslint src/
```

## 项目结构

```
testTools/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── main.py             # 应用入口
│   │   ├── api/v1/curl.py      # curl API 端点
│   │   ├── models/curl.py      # Pydantic 数据模型
│   │   ├── services/curl_parser.py   # curl 解析器
│   │   └── utils/curl_generator.py   # curl 生成器
│   ├── tests/                  # 测试（43 个用例）
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── components/
│   │   │   ├── HomePage/       # 首页（工具卡片列表）
│   │   │   ├── ToolPage/       # 工具页面容器
│   │   │   ├── Layout/         # 布局（Sidebar + MainContent）
│   │   │   └── CurlCoder/      # Curl 工具组件
│   │   ├── hooks/              # API 调用 hooks
│   │   ├── types/              # TypeScript 类型定义
│   │   └── styles/             # 全局样式
│   ├── vite.config.ts
│   └── package.json
└── docs/                       # 文档
    └── deployment.md           # 部署指南
```

## API

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/curl/parse` | 解析 curl 命令 |
| POST | `/api/v1/curl/generate` | 生成 curl 命令 |
| GET | `/health` | 健康检查 |

## License

MIT
