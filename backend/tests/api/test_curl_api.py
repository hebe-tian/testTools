"""curl API 端点集成测试。

使用 httpx AsyncClient 测试 /api/v1/curl/parse 和 /api/v1/curl/generate 端点。
"""

from httpx import AsyncClient


class TestParseEndpoint:
    """curl 解析 API 端点测试。"""

    async def test_parse_success(self, client: AsyncClient) -> None:
        payload = {"curl_text": "curl 'https://api.example.com/users'"}
        response = await client.post("/api/v1/curl/parse", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["method"] == "GET"
        assert data["url"] == "https://api.example.com/users"
        assert data["shell_mode"] == "bash"

    async def test_parse_post_with_body(self, client: AsyncClient) -> None:
        payload = {
            "curl_text": (
                "curl -X POST 'https://api.example.com/users' "
                "-H 'Content-Type: application/json' "
                "-d '{\"name\": \"test\"}'"
            )
        }
        response = await client.post("/api/v1/curl/parse", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["method"] == "POST"
        assert data["body"] is not None
        assert data["body"]["content_type"] == "application/json"

    async def test_parse_empty_input(self, client: AsyncClient) -> None:
        payload = {"curl_text": ""}
        response = await client.post("/api/v1/curl/parse", json=payload)
        assert response.status_code == 422

    async def test_parse_invalid_curl(self, client: AsyncClient) -> None:
        payload = {"curl_text": "not a curl command at all"}
        response = await client.post("/api/v1/curl/parse", json=payload)
        assert response.status_code == 422


class TestGenerateEndpoint:
    """curl 生成 API 端点测试。"""

    async def test_generate_success(self, client: AsyncClient) -> None:
        payload = {
            "method": "GET",
            "url": "https://api.example.com/users",
            "query_params": [],
            "headers": [],
            "cookies": [],
            "shell_mode": "bash",
        }
        response = await client.post("/api/v1/curl/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "curl" in data["curl_text"]
        assert data["shell_mode"] == "bash"

    async def test_generate_post_with_body(self, client: AsyncClient) -> None:
        payload = {
            "method": "POST",
            "url": "https://api.example.com/users",
            "query_params": [],
            "headers": [{"key": "Content-Type", "value": "application/json", "enabled": True}],
            "body": {
                "content_type": "application/json",
                "raw": '{"name": "test"}',
                "json_data": {"name": "test"},
            },
            "cookies": [],
            "shell_mode": "bash",
        }
        response = await client.post("/api/v1/curl/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "-X POST" in data["curl_text"]


class TestRoundTrip:
    """解析+生成闭环测试：解析结果直接用于生成。"""

    async def test_parse_then_generate(self, client: AsyncClient) -> None:
        # 先解析
        parse_payload = {
            "curl_text": (
                "curl -X POST 'https://api.example.com/users' "
                "-H 'Content-Type: application/json' "
                "-d '{\"name\": \"test\"}'"
            )
        }
        parse_response = await client.post("/api/v1/curl/parse", json=parse_payload)
        assert parse_response.status_code == 200
        parsed = parse_response.json()

        # 用解析结果生成
        generate_payload = {
            "method": parsed["method"],
            "url": parsed["url"],
            "query_params": parsed["query_params"],
            "headers": parsed["headers"],
            "body": parsed["body"],
            "auth": parsed["auth"],
            "cookies": parsed["cookies"],
            "shell_mode": parsed["shell_mode"],
        }
        generate_response = await client.post("/api/v1/curl/generate", json=generate_payload)
        assert generate_response.status_code == 200
        generated = generate_response.json()
        assert "curl" in generated["curl_text"]
        assert "POST" in generated["curl_text"]
        assert "api.example.com/users" in generated["curl_text"]
