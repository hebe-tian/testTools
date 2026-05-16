"""curl 解析器单元测试。

覆盖 bash/PowerShell/CMD 多种格式的 curl 命令解析，以及异常场景。
"""

import pytest

from app.services.curl_parser import detect_shell, parse


class TestDetectShell:
    """shell 类型检测测试。"""

    def test_detect_bash(self) -> None:
        curl_text = "curl 'https://example.com'"
        assert detect_shell(curl_text) == "bash"

    def test_detect_powershell_invoke_webrequest(self) -> None:
        curl_text = "Invoke-WebRequest -Uri 'https://example.com'"
        assert detect_shell(curl_text) == "powershell"

    def test_detect_powershell_invoke_restmethod(self) -> None:
        curl_text = "Invoke-RestMethod -Uri 'https://example.com'"
        assert detect_shell(curl_text) == "powershell"

    def test_detect_cmd_curl_exe(self) -> None:
        curl_text = 'curl.exe -X GET "https://example.com"'
        assert detect_shell(curl_text) == "cmd"


class TestParseBashGet:
    """bash 格式 GET 请求解析。"""

    def test_simple_get(self) -> None:
        result = parse("curl 'https://api.example.com/users'")
        assert result.method == "GET"
        assert result.url == "https://api.example.com/users"
        assert result.base_url == "https://api.example.com/users"
        assert result.shell_mode == "bash"

    def test_get_with_query_params(self) -> None:
        result = parse("curl 'https://api.example.com/users?page=1&limit=10'")
        assert result.method == "GET"
        assert result.base_url == "https://api.example.com/users"
        assert len(result.query_params) == 2
        assert result.query_params[0].key == "page"
        assert result.query_params[0].value == "1"
        assert result.query_params[1].key == "limit"
        assert result.query_params[1].value == "10"


class TestParseBashPost:
    """bash 格式 POST 请求解析。"""

    def test_post_with_json_body(self) -> None:
        curl_text = (
            "curl -X POST 'https://api.example.com/users' "
            "-H 'Content-Type: application/json' "
            "-d '{\"name\": \"test\"}'"
        )
        result = parse(curl_text)
        assert result.method == "POST"
        assert result.url == "https://api.example.com/users"
        assert result.body is not None
        assert result.body.content_type == "application/json"
        assert result.body.json_data == {"name": "test"}

    def test_post_with_data_raw(self) -> None:
        curl_text = (
            "curl -X POST 'https://api.example.com/users' "
            "-H 'Content-Type: application/json' "
            "--data-raw '{\"name\": \"test\"}'"
        )
        result = parse(curl_text)
        assert result.method == "POST"
        assert result.body is not None
        assert result.body.json_data == {"name": "test"}


class TestParseBashPut:
    """bash 格式 PUT 请求解析。"""

    def test_put_request(self) -> None:
        curl_text = (
            "curl -X PUT 'https://api.example.com/users/1' "
            "-H 'Content-Type: application/json' "
            "-d '{\"name\": \"updated\"}'"
        )
        result = parse(curl_text)
        assert result.method == "PUT"
        assert result.body is not None
        assert result.body.json_data == {"name": "updated"}


class TestParseBashDelete:
    """bash 格式 DELETE 请求解析。"""

    def test_delete_request(self) -> None:
        curl_text = "curl -X DELETE 'https://api.example.com/users/1'"
        result = parse(curl_text)
        assert result.method == "DELETE"
        assert result.url == "https://api.example.com/users/1"


class TestParseHeaders:
    """请求头解析。"""

    def test_multiple_headers(self) -> None:
        curl_text = (
            "curl 'https://api.example.com' "
            "-H 'Accept: application/json' "
            "-H 'X-Custom-Header: value'"
        )
        result = parse(curl_text)
        assert len(result.headers) == 2
        assert result.headers[0].key == "Accept"
        assert result.headers[0].value == "application/json"
        assert result.headers[1].key == "X-Custom-Header"
        assert result.headers[1].value == "value"


class TestParseAuth:
    """认证信息解析。"""

    def test_bearer_auth(self) -> None:
        curl_text = (
            "curl 'https://api.example.com/users' "
            "-H 'Authorization: Bearer mytoken123'"
        )
        result = parse(curl_text)
        assert result.auth is not None
        assert result.auth.auth_type == "bearer"
        assert result.auth.token == "mytoken123"

    def test_basic_auth(self) -> None:
        curl_text = "curl 'https://api.example.com/users' -u 'myuser:mypass'"
        result = parse(curl_text)
        assert result.auth is not None
        assert result.auth.auth_type == "basic"
        assert result.auth.username == "myuser"
        assert result.auth.password == "mypass"


class TestParseCookies:
    """Cookie 解析。"""

    def test_cookie_with_b_flag(self) -> None:
        curl_text = "curl 'https://api.example.com' -b 'session=abc123; theme=dark'"
        result = parse(curl_text)
        assert len(result.cookies) == 2
        assert result.cookies[0].key == "session"
        assert result.cookies[0].value == "abc123"
        assert result.cookies[1].key == "theme"
        assert result.cookies[1].value == "dark"


class TestParseFormData:
    """表单数据解析。"""

    def test_form_data(self) -> None:
        curl_text = (
            "curl -X POST 'https://api.example.com/upload' "
            "-F 'file=@photo.jpg' "
            "-F 'description=vacation'"
        )
        result = parse(curl_text)
        assert result.method == "POST"
        assert result.body is not None
        assert result.body.form_data is not None
        assert len(result.body.form_data) == 2
        assert result.body.form_data[0].key == "file"
        assert result.body.form_data[0].value == "@photo.jpg"
        assert result.body.form_data[1].key == "description"
        assert result.body.form_data[1].value == "vacation"


class TestParseMultiline:
    """多行续行符解析。"""

    def test_bash_multiline_backslash(self) -> None:
        curl_text = (
            "curl -X POST 'https://api.example.com/users' \\\n"
            "  -H 'Content-Type: application/json' \\\n"
            "  -d '{\"name\": \"test\"}'"
        )
        result = parse(curl_text)
        assert result.method == "POST"
        assert result.body is not None
        assert result.body.json_data == {"name": "test"}


class TestParsePowerShell:
    """PowerShell 格式解析。"""

    def test_invoke_webrequest(self) -> None:
        curl_text = (
            "Invoke-WebRequest -Method Get -Uri 'https://api.example.com/users' "
            "-Headers @{'Accept'='application/json'}"
        )
        result = parse(curl_text)
        assert result.method == "GET"
        assert result.url == "https://api.example.com/users"
        assert result.shell_mode == "powershell"

    def test_invoke_restmethod(self) -> None:
        curl_text = (
            "Invoke-RestMethod -Method Post -Uri 'https://api.example.com/users' "
            "-Headers @{'Content-Type'='application/json'} "
            "-Body '{\"name\": \"test\"}'"
        )
        result = parse(curl_text)
        assert result.method == "POST"
        assert result.body is not None
        assert result.shell_mode == "powershell"


class TestParseCmd:
    """CMD 格式解析。"""

    def test_cmd_format(self) -> None:
        curl_text = (
            'curl.exe -X GET "https://api.example.com/users" '
            '-H "Accept: application/json"'
        )
        result = parse(curl_text)
        assert result.method == "GET"
        assert result.url == "https://api.example.com/users"
        assert result.shell_mode == "cmd"


class TestParseErrors:
    """异常场景测试。"""

    def test_empty_input_raises(self) -> None:
        with pytest.raises(ValueError, match="不能为空"):
            parse("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ValueError, match="不能为空"):
            parse("   \n  ")

    def test_invalid_curl_raises(self) -> None:
        with pytest.raises(ValueError, match="无效的 curl 命令"):
            parse("not a curl command at all")
