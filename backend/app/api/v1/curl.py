"""curl 解析和生成 API 端点。

提供 curl 命令解析和生成的 REST API 接口。
"""

from fastapi import APIRouter, HTTPException

from app.models.curl import (
    CurlGenerateRequest,
    CurlGenerateResponse,
    CurlParseRequest,
    ParsedCurl,
)
from app.services.curl_parser import parse as curl_parse
from app.utils.curl_generator import generate as curl_generate

router = APIRouter()


@router.post("/parse", response_model=ParsedCurl)
async def parse_curl(request: CurlParseRequest) -> ParsedCurl:
    """解析 curl 命令文本为结构化数据。

    Args:
        request: 包含 curl 命令文本的请求体

    Returns:
        ParsedCurl 解析结果

    Raises:
        HTTPException: 输入为空或解析失败时返回 422 错误
    """
    try:
        return curl_parse(request.curl_text)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.post("/generate", response_model=CurlGenerateResponse)
async def generate_curl(request: CurlGenerateRequest) -> CurlGenerateResponse:
    """根据结构化数据生成 curl 命令文本。

    Args:
        request: curl 生成请求数据

    Returns:
        CurlGenerateResponse 包含生成的 curl 命令文本
    """
    curl_text = curl_generate(request)
    return CurlGenerateResponse(curl_text=curl_text, shell_mode=request.shell_mode)
