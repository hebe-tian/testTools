"""pytest 共享 fixtures。

提供测试中常用的 fixture，如异步 HTTP 客户端。
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncClient:
    """创建异步 HTTP 测试客户端，用于测试 API 端点。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
