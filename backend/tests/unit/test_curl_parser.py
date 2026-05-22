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

    def test_chrome_powershell_with_session_variable(self) -> None:
        curl_text = (
            "$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession\n"
            "$session.UserAgent = \"Mozilla/5.0\"\n"
            "Invoke-WebRequest -UseBasicParsing -Uri \"https://api.example.com/users\" `\n"
            " -Method \"POST\" `\n"
            " -WebSession $session `\n"
            " -Headers @{\n"
            "\"Accept\"=\"*/*\"\n"
            "\"Content-Type\"=\"application/json\"\n"
            "} `\n"
            " -ContentType \"application/json\" `\n"
            " -Body '{\"name\": \"test\"}'"
        )
        result = parse(curl_text)
        assert result.method == "POST"
        assert result.url == "https://api.example.com/users"
        assert result.shell_mode == "powershell"
        assert len(result.headers) >= 2
        assert any(h.key == "Accept" for h in result.headers)
        assert any(h.key == "Content-Type" for h in result.headers)
        assert result.body is not None


class TestParsePowerShellChrome:
    """Chrome 复制的 PowerShell 格式解析。

    Chrome DevTools 复制为 PowerShell 时，格式特征：
    - 以 $session 变量赋值开头
    - 使用 Invoke-WebRequest
    - -UseBasicParsing 参数
    - -WebSession $session 引用变量
    - -Headers 使用换行分隔的哈希表
    - 反引号 ` 作为续行符
    """

    def test_chrome_ps_get_request(self) -> None:
        curl_text = (
            "$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession\n"
            "Invoke-WebRequest -UseBasicParsing -Uri \"https://api.example.com/users\" `\n"
            " -Method \"GET\" `\n"
            " -WebSession $session `\n"
            " -Headers @{\n"
            "\"Accept\"=\"application/json\"\n"
            "}"
        )
        result = parse(curl_text)
        assert result.method == "GET"
        assert result.url == "https://api.example.com/users"
        assert result.shell_mode == "powershell"
        assert any(h.key == "Accept" for h in result.headers)

    def test_chrome_ps_post_with_json_body(self) -> None:
        curl_text = (
            "$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession\n"
            "Invoke-WebRequest -UseBasicParsing -Uri \"https://api.example.com/users\" `\n"
            " -Method \"POST\" `\n"
            " -WebSession $session `\n"
            " -Headers @{\n"
            "\"Content-Type\"=\"application/json\"\n"
            "} `\n"
            " -ContentType \"application/json\" `\n"
            " -Body '{\"name\": \"test\"}'"
        )
        result = parse(curl_text)
        assert result.method == "POST"
        assert result.url == "https://api.example.com/users"
        assert result.body is not None
        assert result.body.content_type == "application/json"
        assert result.body.json_data == {"name": "test"}

    def test_chrome_ps_multiple_headers_newline_separated(self) -> None:
        curl_text = (
            "Invoke-WebRequest -UseBasicParsing -Uri \"https://api.example.com\" `\n"
            " -Headers @{\n"
            "\"Accept\"=\"*/*\"\n"
            "\"Accept-Encoding\"=\"gzip, deflate, br, zstd\"\n"
            "\"Accept-Language\"=\"zh-CN,zh;q=0.9,en;q=0.8\"\n"
            "\"Cache-Control\"=\"no-cache\"\n"
            "\"Origin\"=\"https://example.com\"\n"
            "}"
        )
        result = parse(curl_text)
        assert result.url == "https://api.example.com"
        header_keys = [h.key for h in result.headers]
        assert "Accept" in header_keys
        assert "Accept-Encoding" in header_keys
        assert "Accept-Language" in header_keys
        assert "Cache-Control" in header_keys
        assert "Origin" in header_keys
        assert len(result.headers) == 5

    def test_chrome_ps_header_with_special_chars(self) -> None:
        curl_text = (
            "Invoke-WebRequest -UseBasicParsing -Uri \"https://api.example.com\" `\n"
            " -Headers @{\n"
            "\"sec-ch-ua\"=\"\\\"Chromium\\\";v=\\\"148\\\", \\\"Google Chrome\\\";v=\\\"148\\\"\"\n"
            "\"sec-ch-ua-mobile\"=\"?0\"\n"
            "\"sec-ch-ua-platform\"=\"\\\"macOS\\\"\"\n"
            "}"
        )
        result = parse(curl_text)
        header_keys = [h.key for h in result.headers]
        assert "sec-ch-ua" in header_keys
        assert "sec-ch-ua-mobile" in header_keys
        assert "sec-ch-ua-platform" in header_keys

    def test_chrome_ps_usebasicparsing_ignored(self) -> None:
        curl_text = (
            "Invoke-WebRequest -UseBasicParsing -Uri \"https://api.example.com\""
        )
        result = parse(curl_text)
        assert result.url == "https://api.example.com"
        assert result.method == "GET"

    def test_chrome_ps_websession_variable_skipped(self) -> None:
        curl_text = (
            "$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession\n"
            "Invoke-WebRequest -UseBasicParsing -Uri \"https://api.example.com\" `\n"
            " -WebSession $session"
        )
        result = parse(curl_text)
        assert result.url == "https://api.example.com"

    def test_chrome_ps_with_contenttype_and_body(self) -> None:
        curl_text = (
            "Invoke-WebRequest -UseBasicParsing -Uri \"https://api.example.com/data\" `\n"
            " -Method \"POST\" `\n"
            " -Headers @{\n"
            "\"Accept\"=\"*/*\"\n"
            "} `\n"
            " -ContentType \"application/json\" `\n"
            " -Body '{\"key\": \"value\"}'"
        )
        result = parse(curl_text)
        assert result.method == "POST"
        assert result.body is not None
        assert result.body.content_type == "application/json"
        assert result.body.json_data == {"key": "value"}

    def test_chrome_ps_detect_shell_with_session_prefix(self) -> None:
        from app.services.curl_parser import detect_shell

        curl_text = (
            "$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession\n"
            "Invoke-WebRequest -Uri \"https://api.example.com\""
        )
        assert detect_shell(curl_text) == "powershell"

    def test_chrome_ps_backtick_continuation(self) -> None:
        curl_text = (
            "Invoke-WebRequest `\n"
            " -Uri \"https://api.example.com\" `\n"
            " -Method \"GET\""
        )
        result = parse(curl_text)
        assert result.url == "https://api.example.com"
        assert result.method == "GET"

    def test_chrome_ps_semicolon_separated_headers(self) -> None:
        curl_text = (
            "Invoke-WebRequest -Uri \"https://api.example.com\" "
            "-Headers @{'Accept'='application/json'; 'Cache-Control'='no-cache'}"
        )
        result = parse(curl_text)
        assert len(result.headers) == 2
        assert result.headers[0].key == "Accept"
        assert result.headers[1].key == "Cache-Control"

    def test_chrome_ps_mixed_header_separators(self) -> None:
        curl_text = (
            "Invoke-WebRequest -Uri \"https://api.example.com\" "
            "-Headers @{'Accept'='application/json'; 'Cache-Control'='no-cache'; 'Origin'='https://example.com'}"
        )
        result = parse(curl_text)
        assert len(result.headers) == 3


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
