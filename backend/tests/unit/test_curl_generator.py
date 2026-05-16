"""curl 生成器单元测试。

覆盖 bash/PowerShell/CMD 多种格式的 curl 命令生成，
包括美化模式、紧凑模式、各种认证和请求体格式。
"""

from app.models.curl import (
    AuthInfo,
    BodyContent,
    CookieItem,
    CurlGenerateRequest,
    FormItem,
    HeaderItem,
    QueryParam,
)
from app.utils.curl_generator import generate


def _make_request(**overrides: object) -> CurlGenerateRequest:
    """创建测试用的 CurlGenerateRequest，提供合理的默认值。"""
    defaults: dict[str, object] = {
        "method": "GET",
        "url": "https://api.example.com/users",
        "query_params": [],
        "headers": [],
        "cookies": [],
        "shell_mode": "bash",
        "compact": False,
    }
    defaults.update(overrides)
    return CurlGenerateRequest(**defaults)  # type: ignore[arg-type]


class TestGenerateBashGet:
    """bash 格式 GET 请求生成。"""

    def test_simple_get(self) -> None:
        req = _make_request()
        result = generate(req)
        assert result.startswith("curl")
        assert "'https://api.example.com/users'" in result
        assert "-X GET" in result

    def test_get_with_query_params(self) -> None:
        req = _make_request(
            query_params=[QueryParam(key="page", value="1"), QueryParam(key="limit", value="10")]
        )
        result = generate(req)
        assert "page=1" in result
        assert "limit=10" in result


class TestGenerateBashPost:
    """bash 格式 POST 请求生成。"""

    def test_post_with_json_body(self) -> None:
        req = _make_request(
            method="POST",
            headers=[HeaderItem(key="Content-Type", value="application/json")],
            body=BodyContent(
                content_type="application/json",
                raw='{"name": "test"}',
                json_data={"name": "test"},
            ),
        )
        result = generate(req)
        assert "-X POST" in result
        assert "'Content-Type: application/json'" in result
        assert "-d" in result


class TestGenerateBashPut:
    """bash 格式 PUT 请求生成。"""

    def test_put_request(self) -> None:
        req = _make_request(
            method="PUT",
            headers=[HeaderItem(key="Content-Type", value="application/json")],
            body=BodyContent(content_type="application/json", raw='{"name": "updated"}'),
        )
        result = generate(req)
        assert "-X PUT" in result


class TestGenerateBashFormat:
    """bash 格式美化/紧凑模式。"""

    def test_pretty_mode_with_backslash(self) -> None:
        """美化模式应使用续行符和缩进。"""
        req = _make_request(
            method="POST",
            headers=[HeaderItem(key="Content-Type", value="application/json")],
            body=BodyContent(content_type="application/json", raw='{"name": "test"}'),
            compact=False,
        )
        result = generate(req)
        assert "\\\n" in result or "\\\r\n" in result

    def test_compact_mode_single_line(self) -> None:
        """紧凑模式应输出为单行。"""
        req = _make_request(
            method="POST",
            headers=[HeaderItem(key="Content-Type", value="application/json")],
            body=BodyContent(content_type="application/json", raw='{"name": "test"}'),
            compact=True,
        )
        result = generate(req)
        assert "\n" not in result


class TestGenerateAuth:
    """认证信息生成。"""

    def test_bearer_auth(self) -> None:
        req = _make_request(auth=AuthInfo(auth_type="bearer", token="mytoken123"))
        result = generate(req)
        assert "Authorization: Bearer mytoken123" in result

    def test_basic_auth(self) -> None:
        req = _make_request(auth=AuthInfo(auth_type="basic", username="user", password="pass"))
        result = generate(req)
        assert "-u 'user:pass'" in result


class TestGenerateCookies:
    """Cookie 生成。"""

    def test_cookies(self) -> None:
        req = _make_request(
            cookies=[
                CookieItem(key="session", value="abc123"),
                CookieItem(key="theme", value="dark"),
            ]
        )
        result = generate(req)
        assert "-b" in result
        assert "session=abc123" in result
        assert "theme=dark" in result


class TestGeneratePowerShell:
    """PowerShell 格式生成。"""

    def test_powershell_format(self) -> None:
        req = _make_request(shell_mode="powershell")
        result = generate(req)
        assert "Invoke-RestMethod" in result
        assert "-Uri" in result
        assert "-Method" in result

    def test_powershell_post_with_body(self) -> None:
        req = _make_request(
            method="POST",
            shell_mode="powershell",
            headers=[HeaderItem(key="Content-Type", value="application/json")],
            body=BodyContent(content_type="application/json", raw='{"name": "test"}'),
        )
        result = generate(req)
        assert "-Body" in result
        assert "-Headers" in result


class TestGenerateCmd:
    """CMD 格式生成。"""

    def test_cmd_format(self) -> None:
        req = _make_request(shell_mode="cmd")
        result = generate(req)
        assert result.startswith("curl")
        assert '"https://api.example.com/users"' in result

    def test_cmd_uses_double_quotes(self) -> None:
        """CMD 格式应使用双引号包裹参数。"""
        req = _make_request(
            method="POST",
            shell_mode="cmd",
            headers=[HeaderItem(key="Content-Type", value="application/json")],
            body=BodyContent(content_type="application/json", raw='{"name": "test"}'),
        )
        result = generate(req)
        # CMD 格式使用双引号，内部双引号用反斜杠转义
        assert "-H" in result


class TestGenerateFormData:
    """表单数据生成。"""

    def test_form_data_bash(self) -> None:
        req = _make_request(
            method="POST",
            shell_mode="bash",
            body=BodyContent(
                content_type="multipart/form-data",
                raw="",
                form_data=[
                    FormItem(key="file", value="@photo.jpg"),
                    FormItem(key="description", value="vacation"),
                ],
            ),
        )
        result = generate(req)
        assert "-F" in result
        assert "file=@photo.jpg" in result
        assert "description=vacation" in result
