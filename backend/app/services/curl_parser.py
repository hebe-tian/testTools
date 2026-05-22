"""curl 命令解析器。

支持 bash、PowerShell、CMD 三种 shell 格式的 curl 命令解析，
将 curl 命令文本转换为结构化的 ParsedCurl 数据模型。
"""

import json
import re
import shlex
from urllib.parse import parse_qs, urlparse, urlunparse

from app.models.curl import (
    AuthInfo,
    BodyContent,
    CookieItem,
    FormItem,
    HeaderItem,
    ParsedCurl,
    QueryParam,
)


def detect_shell(curl_text: str) -> str:
    """检测 curl 命令的 shell 类型。

    根据命令中的特征关键词判断 shell 类型：
    - 包含 Invoke-WebRequest 或 Invoke-RestMethod → powershell
    - 包含 curl.exe → cmd
    - 其他 → bash

    Args:
        curl_text: curl 命令文本

    Returns:
        shell 类型字符串: "bash" / "powershell" / "cmd"
    """
    if "Invoke-WebRequest" in curl_text or "Invoke-RestMethod" in curl_text:
        return "powershell"
    if "curl.exe" in curl_text:
        return "cmd"
    return "bash"


def split_args(curl_text: str, shell_mode: str) -> list[str]:
    """将 curl 命令文本拆分为参数列表。

    根据不同 shell 类型处理续行符和引号规则：
    - bash: 处理 \\ 续行符、单引号/双引号包裹
    - powershell: 处理反引号续行、单引号/双引号
    - cmd: 处理 ^ 续行、双引号

    Args:
        curl_text: curl 命令文本
        shell_mode: shell 类型

    Returns:
        参数列表
    """
    text = curl_text.strip()

    if shell_mode == "bash":
        # 移除 bash 续行符：反斜杠后跟换行
        text = re.sub(r"\\\s*\n", " ", text)
        # 移除 curl 命令前缀
        text = re.sub(r"^\s*curl\s*", "", text)
        return _split_with_quotes(text)

    if shell_mode == "powershell":
        # 移除 PowerShell 反引号续行
        text = re.sub(r"`\s*\n", " ", text)
        # 移除 Invoke-WebRequest / Invoke-RestMethod 前缀
        text = re.sub(r"^\s*Invoke-(?:WebRequest|RestMethod)\s*", "", text)
        return _split_powershell_args(text)

    if shell_mode == "cmd":
        # 移除 CMD 续行符 ^ 后跟换行
        text = re.sub(r"\^\s*\n", " ", text)
        # 移除 curl.exe 前缀
        text = re.sub(r"^\s*curl\.exe\s*", "", text)
        return _split_cmd_args(text)

    return _split_with_quotes(text)


def _split_with_quotes(text: str) -> list[str]:
    """使用 shlex 拆分参数，兼容单引号和双引号。

    shlex 在 posix 模式下能正确处理单引号和双引号包裹的参数。

    Args:
        text: 已移除命令前缀和续行符的参数文本

    Returns:
        参数列表
    """
    try:
        return shlex.split(text, posix=True)
    except ValueError:
        # shlex 解析失败时，使用简单空格拆分作为回退
        return text.split()


def _split_powershell_args(text: str) -> list[str]:
    """拆分 PowerShell 格式的参数。

    处理 PowerShell 特有的参数格式，如 -Method Get、
    -Headers @{'Key'='Value'}、-Body 'content' 等。

    Args:
        text: 已移除命令前缀的参数文本

    Returns:
        参数列表
    """
    args: list[str] = []
    current = ""
    i = 0
    in_hashtable = 0  # 哈希表嵌套层级计数器

    while i < len(text):
        char = text[i]

        # 处理哈希表 @{ ... }
        if char == "@" and i + 1 < len(text) and text[i + 1] == "{":
            in_hashtable += 1
            current += "@{"
            i += 2
            continue

        if in_hashtable > 0:
            if char == "{":
                in_hashtable += 1
            elif char == "}":
                in_hashtable -= 1
            current += char
            i += 1
            # 哈希表结束时，将当前参数加入列表
            if in_hashtable == 0:
                args.append(current.strip())
                current = ""
            continue

        # 处理单引号包裹的字符串
        if char == "'":
            end = text.find("'", i + 1)
            if end == -1:
                current += text[i:]
                break
            current += text[i : end + 1]
            i = end + 1
            continue

        # 处理双引号包裹的字符串
        if char == '"':
            end = text.find('"', i + 1)
            if end == -1:
                current += text[i:]
                break
            current += text[i : end + 1]
            i = end + 1
            continue

        # 空格作为参数分隔符
        if char in (" ", "\t", "\n"):
            if current.strip():
                args.append(current.strip())
                current = ""
            i += 1
            continue

        current += char
        i += 1

    if current.strip():
        args.append(current.strip())

    return args


def _split_cmd_args(text: str) -> list[str]:
    """拆分 CMD 格式的参数。

    CMD 格式使用双引号包裹参数，内部双引号用反斜杠转义。

    Args:
        text: 已移除命令前缀的参数文本

    Returns:
        参数列表
    """
    args: list[str] = []
    current = ""
    in_quotes = False
    i = 0

    while i < len(text):
        char = text[i]

        if char == '"':
            in_quotes = not in_quotes
            current += char
            i += 1
            continue

        # 处理转义双引号 \"
        if char == "\\" and i + 1 < len(text) and text[i + 1] == '"':
            current += '\\"'
            i += 2
            continue

        # 非引号内的空格作为分隔符
        if char in (" ", "\t", "\n") and not in_quotes:
            if current.strip():
                args.append(current.strip())
                current = ""
            i += 1
            continue

        current += char
        i += 1

    if current.strip():
        args.append(current.strip())

    # 去除 CMD 参数两端的双引号
    cleaned: list[str] = []
    for arg in args:
        if arg.startswith('"') and arg.endswith('"') and len(arg) > 1:
            cleaned.append(arg[1:-1])
        else:
            cleaned.append(arg)
    return cleaned


def _strip_quotes(value: str) -> str:
    """去除字符串两端的引号（单引号或双引号）。

    Args:
        value: 可能被引号包裹的字符串

    Returns:
        去除引号后的字符串
    """
    if len(value) >= 2:
        if (value[0] == "'" and value[-1] == "'") or (value[0] == '"' and value[-1] == '"'):
            return value[1:-1]
    return value


def _unescape_powershell(value: str) -> str:
    """处理 PowerShell 反引号转义序列。

    PowerShell 反引号转义规则：
    - `" → 双引号
    - `$ → 美元符号
    - `` → 反引号本身
    - `n → 换行
    - `t → 制表符
    - `r → 回车
    - 其他 `X → X（反引号被移除）

    Args:
        value: 包含 PowerShell 转义序列的字符串

    Returns:
        处理转义后的字符串
    """
    result: list[str] = []
    i = 0
    while i < len(value):
        if value[i] == "`" and i + 1 < len(value):
            next_char = value[i + 1]
            escape_map = {
                '"': '"',
                "'": "'",
                "$": "$",
                "`": "`",
                "n": "\n",
                "t": "\t",
                "r": "\r",
                "\\": "\\",
                "0": "\0",
                "a": "\a",
                "b": "\b",
                "f": "\f",
                "v": "\v",
            }
            result.append(escape_map.get(next_char, next_char))
            i += 2
        else:
            result.append(value[i])
            i += 1
    return "".join(result)


def _parse_url_query(url: str) -> tuple[str, list[QueryParam]]:
    """从 URL 中提取 base_url 和查询参数。

    Args:
        url: 完整的 URL，可能包含查询字符串

    Returns:
        (base_url, query_params) 元组
    """
    parsed = urlparse(url)
    params: list[QueryParam] = []

    if parsed.query:
        qs = parse_qs(parsed.query, keep_blank_values=True)
        for key, values in qs.items():
            for v in values:
                params.append(QueryParam(key=key, value=v))

    # 重建不含查询参数的 base_url
    base = urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, "", parsed.fragment)
    )
    return base, params


def _parse_cookie_string(cookie_str: str) -> list[CookieItem]:
    """解析 Cookie 字符串为 CookieItem 列表。

    Cookie 字符串格式为 "key1=value1; key2=value2"。

    Args:
        cookie_str: Cookie 字符串

    Returns:
        CookieItem 列表
    """
    cookies: list[CookieItem] = []
    for pair in cookie_str.split(";"):
        pair = pair.strip()
        if "=" in pair:
            key, _, value = pair.partition("=")
            cookies.append(CookieItem(key=key.strip(), value=value.strip()))
    return cookies


def _extract_auth_from_headers(headers: list[HeaderItem]) -> AuthInfo | None:
    """从请求头中提取认证信息。

    支持的认证类型：
    - Bearer Token: Authorization: Bearer <token>
    - Basic Auth: Authorization: Basic <encoded>

    Args:
        headers: 请求头列表

    Returns:
        AuthInfo 对象，如果没有认证头则返回 None
    """
    for h in headers:
        if h.key.lower() == "authorization":
            value = h.value.strip()
            if value.startswith("Bearer "):
                return AuthInfo(auth_type="bearer", token=value[7:].strip())
            if value.startswith("Basic "):
                import base64

                try:
                    decoded = base64.b64decode(value[6:].strip()).decode("utf-8")
                    username, _, password = decoded.partition(":")
                    return AuthInfo(auth_type="basic", username=username, password=password)
                except Exception:
                    return AuthInfo(auth_type="basic", token=value[6:].strip())
    return None


def _try_parse_json(raw: str) -> dict[str, object] | list[object] | None:
    """尝试将字符串解析为 JSON。

    Args:
        raw: 待解析的字符串

    Returns:
        解析后的字典或列表，解析失败返回 None
    """
    try:
        result = json.loads(raw)
        if isinstance(result, (dict, list)):
            return result
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def parse(curl_text: str) -> ParsedCurl:
    """解析 curl 命令文本为结构化数据。

    主解析函数，自动检测 shell 类型，拆分参数，
    遍历参数映射到 ParsedCurl 各字段。

    Args:
        curl_text: curl 命令文本

    Returns:
        ParsedCurl 解析结果

    Raises:
        ValueError: 输入为空或不是有效的 curl 命令
    """
    # 输入校验
    if not curl_text or not curl_text.strip():
        raise ValueError("curl 命令文本不能为空")

    # 校验是否为有效的 curl 命令格式
    stripped = curl_text.strip()
    if not (
        stripped.startswith("curl")
        or "Invoke-WebRequest" in stripped
        or "Invoke-RestMethod" in stripped
    ):
        raise ValueError(
            "无效的 curl 命令：必须包含 curl、Invoke-WebRequest 或 Invoke-RestMethod"
        )

    # 检测 shell 类型
    shell_mode = detect_shell(curl_text)

    # PowerShell 使用独立的解析逻辑
    if shell_mode == "powershell":
        return _parse_powershell(curl_text)

    # bash / cmd 使用通用解析逻辑
    args = split_args(curl_text, shell_mode)

    # 校验是否为有效的 curl 命令（至少需要 URL）
    if not args:
        raise ValueError("无效的 curl 命令：未找到任何参数")

    method = "GET"
    url = ""
    headers: list[HeaderItem] = []
    body_raw = ""
    body_content_type = ""
    cookies: list[CookieItem] = []
    form_items: list[FormItem] = []
    auth_user_pass: str | None = None

    i = 0
    while i < len(args):
        arg = args[i]

        # -X / --request: HTTP 方法
        if arg in ("-X", "--request"):
            i += 1
            if i < len(args):
                method = args[i].upper()

        # -H / --header: 请求头
        elif arg in ("-H", "--header"):
            i += 1
            if i < len(args):
                header_val = _strip_quotes(args[i])
                if ":" in header_val:
                    key, _, value = header_val.partition(":")
                    headers.append(HeaderItem(key=key.strip(), value=value.strip()))

        # -d / --data / --data-raw / --data-binary: 请求体
        elif arg in ("-d", "--data", "--data-raw", "--data-binary"):
            i += 1
            if i < len(args):
                body_raw = _strip_quotes(args[i])
                # 有 -d 时默认方法为 POST
                if method == "GET":
                    method = "POST"

        # -F / --form: 表单数据
        elif arg in ("-F", "--form"):
            i += 1
            if i < len(args):
                form_val = _strip_quotes(args[i])
                if "=" in form_val:
                    key, _, value = form_val.partition("=")
                    form_items.append(FormItem(key=key, value=value))
                # 有 -F 时默认方法为 POST
                if method == "GET":
                    method = "POST"

        # -b / --cookie: Cookie
        elif arg in ("-b", "--cookie"):
            i += 1
            if i < len(args):
                cookie_str = _strip_quotes(args[i])
                cookies = _parse_cookie_string(cookie_str)

        # -u / --user: Basic 认证
        elif arg in ("-u", "--user"):
            i += 1
            if i < len(args):
                auth_user_pass = _strip_quotes(args[i])

        # URL 参数（不以 - 开头的参数）
        elif not arg.startswith("-") and not url:
            url = _strip_quotes(arg)

        i += 1

    # 校验 URL
    if not url:
        raise ValueError("无效的 curl 命令：未找到 URL")

    # 解析 URL 中的查询参数
    base_url, query_params = _parse_url_query(url)

    # 从 Content-Type 头推断 body 类型
    for h in headers:
        if h.key.lower() == "content-type":
            body_content_type = h.value.split(";")[0].strip()
            break

    # 如果有 form-data 但没有 Content-Type，设置为 multipart/form-data
    if form_items and not body_content_type:
        body_content_type = "multipart/form-data"

    # 如果有 body 数据但没有 Content-Type，默认为 application/x-www-form-urlencoded
    if body_raw and not body_content_type:
        body_content_type = "application/x-www-form-urlencoded"

    # 构建 BodyContent
    body: BodyContent | None = None
    if body_raw or form_items:
        json_data = _try_parse_json(body_raw) if body_raw else None
        body = BodyContent(
            content_type=body_content_type,
            raw=body_raw,
            json_data=json_data,
            form_data=form_items if form_items else None,
        )

    # 提取认证信息
    auth = _extract_auth_from_headers(headers)

    # 处理 -u 参数的 Basic Auth
    if auth_user_pass and not auth:
        username, _, password = auth_user_pass.partition(":")
        auth = AuthInfo(auth_type="basic", username=username, password=password)

    # 从认证头列表中移除 Authorization 头（已提取到 auth 字段）
    filtered_headers = [h for h in headers if h.key.lower() != "authorization"]

    return ParsedCurl(
        method=method,
        url=url,
        base_url=base_url,
        query_params=query_params,
        headers=filtered_headers,
        body=body,
        auth=auth,
        cookies=cookies,
        shell_mode=shell_mode,
    )


def _parse_powershell(curl_text: str) -> ParsedCurl:
    """解析 PowerShell 格式的 curl 命令。

    支持 Invoke-WebRequest 和 Invoke-RestMethod 两种命令格式。

    Args:
        curl_text: PowerShell 格式的 curl 命令文本

    Returns:
        ParsedCurl 解析结果
    """
    text = curl_text.strip()
    # 移除续行符
    text = re.sub(r"`\s*\n", " ", text)
    # 找到 Invoke-WebRequest / Invoke-RestMethod 的位置，移除之前的变量赋值
    match = re.search(r"Invoke-(?:WebRequest|RestMethod)\s*", text)
    if match:
        text = text[match.end():]

    method = "GET"
    url = ""
    headers: list[HeaderItem] = []
    body_raw = ""
    body_content_type = ""
    cookies: list[CookieItem] = []

    args = _split_powershell_args(text)

    i = 0
    while i < len(args):
        arg = args[i]

        # -Method: HTTP 方法
        if arg == "-Method":
            i += 1
            if i < len(args):
                method = _unescape_powershell(args[i].strip("'\"")).upper()

        # -Uri: 请求 URL
        elif arg == "-Uri":
            i += 1
            if i < len(args):
                url = _unescape_powershell(_strip_quotes(args[i]))

        # -Headers: 请求头（PowerShell 哈希表格式）
        elif arg == "-Headers":
            i += 1
            if i < len(args):
                headers = _parse_powershell_headers(args[i])

        # -Body: 请求体
        elif arg == "-Body":
            i += 1
            if i < len(args):
                body_raw = _unescape_powershell(_strip_quotes(args[i]))
                if method == "GET":
                    method = "POST"

        # -ContentType: 内容类型
        elif arg == "-ContentType":
            i += 1
            if i < len(args):
                body_content_type = _unescape_powershell(_strip_quotes(args[i]))

        # -Cookie / -WebSession: Cookie（简化处理，-WebSession 跳过变量引用）
        elif arg in ("-Cookie", "-WebSession", "-UseBasicParsing"):
            if arg == "-Cookie":
                i += 1
                if i < len(args):
                    cookie_str = _strip_quotes(args[i])
                    cookies = _parse_cookie_string(cookie_str)
            elif arg == "-WebSession":
                i += 1

        i += 1

    if not url:
        raise ValueError("无效的 curl 命令：未找到 URL")

    base_url, query_params = _parse_url_query(url)

    # 从请求头提取 Content-Type
    for h in headers:
        if h.key.lower() == "content-type":
            body_content_type = h.value.split(";")[0].strip()
            break

    if body_raw and not body_content_type:
        body_content_type = "application/json"

    body: BodyContent | None = None
    if body_raw:
        json_data = _try_parse_json(body_raw)
        body = BodyContent(
            content_type=body_content_type,
            raw=body_raw,
            json_data=json_data,
        )

    auth = _extract_auth_from_headers(headers)
    filtered_headers = [h for h in headers if h.key.lower() != "authorization"]

    return ParsedCurl(
        method=method,
        url=url,
        base_url=base_url,
        query_params=query_params,
        headers=filtered_headers,
        body=body,
        auth=auth,
        cookies=cookies,
        shell_mode="powershell",
    )


def _parse_powershell_headers(header_arg: str) -> list[HeaderItem]:
    """解析 PowerShell 哈希表格式的请求头。

    格式示例:
    - 分号分隔: @{'Content-Type'='application/json'; 'Accept'='text/html'}
    - 换行分隔（Chrome 格式）: @{"Content-Type"="application/json"
        "Accept"="text/html"}

    Args:
        header_arg: PowerShell 哈希表字符串

    Returns:
        HeaderItem 列表
    """
    headers: list[HeaderItem] = []
    inner = header_arg.strip()
    if inner.startswith("@{") and inner.endswith("}"):
        inner = inner[2:-1]

    # 将换行统一替换为分号，兼容 Chrome 的换行分隔格式
    inner = inner.replace("\n", ";")

    # 按分号拆分，跳过引号内的分号，同时正确处理反引号转义引号
    pairs = _split_respecting_quotes(inner, ";")
    for pair in pairs:
        pair = pair.strip()
        if "=" in pair:
            key, _, value = pair.partition("=")
            key = _unescape_powershell(_strip_outer_quotes(key.strip()))
            value = _unescape_powershell(_strip_outer_quotes(value.strip()))
            if key:
                headers.append(HeaderItem(key=key, value=value))

    return headers


def _split_respecting_quotes(text: str, delimiter: str) -> list[str]:
    """按分隔符拆分字符串，但跳过引号内的分隔符。

    同时处理 PowerShell 反引号转义：`" 不视为引号边界。

    Args:
        text: 待拆分的字符串
        delimiter: 分隔符

    Returns:
        拆分后的字符串列表
    """
    parts: list[str] = []
    current = ""
    in_single = False
    in_double = False

    i = 0
    while i < len(text):
        char = text[i]

        if char == "`" and i + 1 < len(text):
            current += char + text[i + 1]
            i += 2
            continue

        if char == "'" and not in_double:
            in_single = not in_single
            current += char
        elif char == '"' and not in_single:
            in_double = not in_double
            current += char
        elif char == delimiter and not in_single and not in_double:
            if current.strip():
                parts.append(current.strip())
            current = ""
        else:
            current += char

        i += 1

    if current.strip():
        parts.append(current.strip())

    return parts


def _strip_outer_quotes(text: str) -> str:
    """只剥离一对匹配的外层引号，不贪婪删除。

    Args:
        text: 待处理的字符串

    Returns:
        剥离外层引号后的字符串
    """
    if len(text) >= 2:
        if (text[0] == '"' and text[-1] == '"') or (text[0] == "'" and text[-1] == "'"):
            return text[1:-1]
    return text
