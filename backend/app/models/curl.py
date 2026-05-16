"""curl 解析结果数据模型。

定义 curl 命令解析后的结构化数据模型，用于 API 请求和响应。
"""

from pydantic import BaseModel


class QueryParam(BaseModel):
    """URL 查询参数。"""

    key: str
    value: str
    enabled: bool = True


class HeaderItem(BaseModel):
    """HTTP 请求头项。"""

    key: str
    value: str
    enabled: bool = True


class FormItem(BaseModel):
    """表单数据项。"""

    key: str
    value: str
    enabled: bool = True


class CookieItem(BaseModel):
    """Cookie 项。"""

    key: str
    value: str
    enabled: bool = True


class BodyContent(BaseModel):
    """HTTP 请求体内容。"""

    content_type: str
    raw: str
    json_data: dict[str, object] | list[object] | None = None
    form_data: list[FormItem] | None = None


class AuthInfo(BaseModel):
    """认证信息。"""

    auth_type: str
    token: str | None = None
    username: str | None = None
    password: str | None = None
    key_name: str | None = None
    key_value: str | None = None
    key_location: str | None = None


class ParsedCurl(BaseModel):
    """curl 命令解析结果。"""

    method: str
    url: str
    base_url: str
    query_params: list[QueryParam]
    headers: list[HeaderItem]
    body: BodyContent | None = None
    auth: AuthInfo | None = None
    cookies: list[CookieItem]
    shell_mode: str


class CurlParseRequest(BaseModel):
    """curl 解析请求。"""

    curl_text: str


class CurlGenerateRequest(BaseModel):
    """curl 生成请求。"""

    method: str
    url: str
    query_params: list[QueryParam]
    headers: list[HeaderItem]
    body: BodyContent | None = None
    auth: AuthInfo | None = None
    cookies: list[CookieItem]
    shell_mode: str = "bash"
    compact: bool = False


class CurlGenerateResponse(BaseModel):
    """curl 生成响应。"""

    curl_text: str
    shell_mode: str
