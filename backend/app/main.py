"""testTools 后端应用入口模块。

负责创建 FastAPI 应用实例，配置 CORS、注册路由等。
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.curl import router as curl_router

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app = FastAPI(
    title="testTools",
    description="测试工具集 Web 应用后端",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(curl_router, prefix="/api/v1/curl", tags=["curl"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    """健康检查端点，用于确认服务是否正常运行。"""
    return {"status": "ok"}
