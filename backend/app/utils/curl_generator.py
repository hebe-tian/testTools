"""curl 命令生成器。

将结构化的 CurlGenerateRequest 数据模型转换为 curl 命令文本，
支持 bash、PowerShell、CMD 三种 shell 格式输出。
"""

import json
from urllib.parse import urlencode, urlparse, urlunparse

from app.models.curl import CurlGenerateRequest


def generate(data: CurlGenerateRequest) -> str:
    """根据请求数据生成 curl 命令文本。

    根据 shell_mode 选择对应的格式化方式：
    - bash: 使用单引号包裹，续行符为 \\
    - powershell: 使用 Invoke-RestMethod，哈希表格式请求头
    - cmd: 使用双引号包裹，内部双引号反斜杠转义

    Args:
        data: curl 生成请求数据

    Returns:
        生成的 curl 命令文本
    """
    if data.shell_mode == "powershell":
        return _generate_powershell(data)
    if data.shell_mode == "cmd":
        return _generate_cmd(data)
    return _generate_bash(data)


def _build_full_url(data: CurlGenerateRequest) -> str:
    """构建包含查询参数的完整 URL。

    如果请求中包含查询参数，将其拼接到 URL 上。

    Args:
        data: curl 生成请求数据

    Returns:
        带查询参数的完整 URL
    """
    url = data.url
    # 如果 URL 中已有查询参数，先提取出来
    parsed = urlparse(url)
    existing_params: dict[str, str] = {}

    # 解析 URL 中已有的查询参数
    if parsed.query:
        for pair in parsed.query.split("&"):
            if "=" in pair:
                k, _, v = pair.partition("=")
                existing_params[k] = v

    # 合并请求中的查询参数（仅启用状态的）
    for qp in data.query_params:
        if qp.enabled:
            existing_params[qp.key] = qp.value

    # 重建 URL
    if existing_params:
        query_string = urlencode(existing_params)
        url = urlunparse((
            parsed.scheme, parsed.netloc, parsed.path, parsed.params, query_string, parsed.fragment
        ))

    return url


def _generate_bash(data: CurlGenerateRequest) -> str:
    """生成 bash 格式的 curl 命令。

    bash 格式特点：
    - 使用单引号包裹 URL 和参数值
    - 美化模式使用反斜杠续行符 + 双空格缩进
    - 紧凑模式输出为单行

    Args:
        data: curl 生成请求数据

    Returns:
        bash 格式的 curl 命令文本
    """
    parts: list[str] = []
    url = _build_full_url(data)

    # HTTP 方法
    parts.append(f"curl -X {data.method}")
    # URL
    parts.append(f"'{url}'")

    # 认证信息 - Bearer Token 通过请求头传递
    if data.auth:
        if data.auth.auth_type == "bearer" and data.auth.token:
            parts.append(f"-H 'Authorization: Bearer {data.auth.token}'")
        elif data.auth.auth_type == "basic" and data.auth.username is not None:
            password = data.auth.password or ""
            parts.append(f"-u '{data.auth.username}:{password}'")

    # 请求头
    for h in data.headers:
        if h.enabled:
            parts.append(f"-H '{h.key}: {h.value}'")

    # Cookie
    if data.cookies:
        enabled_cookies = [c for c in data.cookies if c.enabled]
        if enabled_cookies:
            cookie_str = "; ".join(f"{c.key}={c.value}" for c in enabled_cookies)
            parts.append(f"-b '{cookie_str}'")

    # 请求体
    if data.body:
        # form-data 使用 -F 参数
        if data.body.form_data:
            for item in data.body.form_data:
                if item.enabled:
                    parts.append(f"-F '{item.key}={item.value}'")
        # 其他请求体使用 -d 参数
        elif data.body.raw:
            raw = data.body.raw
            # 如果有 json_data，使用格式化的 JSON
            if data.body.json_data is not None:
                raw = json.dumps(data.body.json_data, ensure_ascii=False)
            parts.append(f"-d '{raw}'")

    # 格式化输出
    if data.compact:
        return " ".join(parts)
    # 美化模式：续行符 + 缩进
    return " \\\n  ".join(parts)


def _generate_powershell(data: CurlGenerateRequest) -> str:
    """生成 PowerShell 格式的 curl 命令。

    使用 Invoke-RestMethod 命令格式，请求头使用哈希表语法。

    Args:
        data: curl 生成请求数据

    Returns:
        PowerShell 格式的 curl 命令文本
    """
    parts: list[str] = []
    url = _build_full_url(data)

    # 方法名映射为 PowerShell 首字母大写格式
    method_map: dict[str, str] = {
        "GET": "Get",
        "POST": "Post",
        "PUT": "Put",
        "DELETE": "Delete",
        "PATCH": "Patch",
        "HEAD": "Head",
        "OPTIONS": "Options",
    }
    ps_method = method_map.get(data.method.upper(), data.method.capitalize())

    parts.append("Invoke-RestMethod")
    parts.append(f"-Method {ps_method}")
    parts.append(f"-Uri '{url}'")

    # 收集所有请求头（包括认证头）
    all_headers: dict[str, str] = {}
    if data.auth and data.auth.auth_type == "bearer" and data.auth.token:
        all_headers["Authorization"] = f"Bearer {data.auth.token}"

    for h in data.headers:
        if h.enabled:
            all_headers[h.key] = h.value

    if all_headers:
        header_pairs = "; ".join(f"'{k}'='{v}'" for k, v in all_headers.items())
        parts.append(f"-Headers @{{{header_pairs}}}")

    # 请求体
    if data.body and data.body.raw:
        raw = data.body.raw
        if data.body.json_data is not None:
            raw = json.dumps(data.body.json_data, ensure_ascii=False)
        parts.append(f"-Body '{raw}'")

    # 紧凑模式
    if data.compact:
        return " ".join(parts)
    return " `\n  ".join(parts)


def _generate_cmd(data: CurlGenerateRequest) -> str:
    """生成 CMD 格式的 curl 命令。

    CMD 格式特点：
    - 使用双引号包裹参数
    - 内部双引号用反斜杠转义
    - 续行符为 ^

    Args:
        data: curl 生成请求数据

    Returns:
        CMD 格式的 curl 命令文本
    """
    parts: list[str] = []
    url = _build_full_url(data)

    parts.append(f"curl -X {data.method}")
    # CMD 使用双引号包裹 URL
    parts.append(f'"{url}"')

    # 认证信息
    if data.auth:
        if data.auth.auth_type == "bearer" and data.auth.token:
            parts.append(f'-H "Authorization: Bearer {data.auth.token}"')
        elif data.auth.auth_type == "basic" and data.auth.username is not None:
            password = data.auth.password or ""
            parts.append(f'-u "{data.auth.username}:{password}"')

    # 请求头（CMD 双引号包裹，内部双引号转义）
    for h in data.headers:
        if h.enabled:
            escaped_value = h.value.replace('"', '\\"')
            parts.append(f'-H "{h.key}: {escaped_value}"')

    # Cookie
    if data.cookies:
        enabled_cookies = [c for c in data.cookies if c.enabled]
        if enabled_cookies:
            cookie_str = "; ".join(f"{c.key}={c.value}" for c in enabled_cookies)
            parts.append(f'-b "{cookie_str}"')

    # 请求体
    if data.body:
        if data.body.form_data:
            for item in data.body.form_data:
                if item.enabled:
                    parts.append(f'-F "{item.key}={item.value}"')
        elif data.body.raw:
            raw = data.body.raw
            if data.body.json_data is not None:
                raw = json.dumps(data.body.json_data, ensure_ascii=False)
            # CMD 中双引号需要转义
            escaped_raw = raw.replace('"', '\\"')
            parts.append(f'-d "{escaped_raw}"')

    # 格式化输出
    if data.compact:
        return " ".join(parts)
    # CMD 美化模式使用 ^ 续行符
    return " ^\n  ".join(parts)
