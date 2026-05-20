"""Cloudflare Worker 入口文件 - 处理 testTools 后端 API 请求"""

import json
from workers import WorkerEntrypoint, Response


class Default(WorkerEntrypoint):
    """默认的 Worker 入口类，处理所有 HTTP 请求"""

    async def fetch(self, request):
        """处理所有入站请求的路由分发"""
        url = str(request.url)
        method = request.method

        cors_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }

        if method == "OPTIONS":
            return Response("", status=204, headers=cors_headers)

        if url.endswith("/health"):
            return Response(
                json.dumps({"status": "ok"}),
                headers={"Content-Type": "application/json", **cors_headers}
            )

        if url.endswith("/api/v1/curl/parse") and method == "POST":
            resp = await self._handle_parse(request)
            return resp

        if url.endswith("/api/v1/curl/generate") and method == "POST":
            resp = await self._handle_generate(request)
            return resp

        return Response("Not Found", status=404, headers=cors_headers)

    async def _handle_parse(self, request):
        """处理 curl 解析请求"""
        cors_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
        try:
            body = await request.json()
            curl_text = body.get("curl_text", "")

            from app.services.curl_parser import parse
            result = parse(curl_text)

            return Response(
                result.model_dump_json(),
                headers={"Content-Type": "application/json", **cors_headers}
            )
        except Exception as e:
            return Response(
                json.dumps({"detail": str(e)}),
                status=400,
                headers={"Content-Type": "application/json", **cors_headers}
            )

    async def _handle_generate(self, request):
        """处理 curl 生成请求"""
        cors_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
        try:
            body = await request.json()

            from app.utils.curl_generator import generate
            from app.models.curl import CurlGenerateRequest

            req = CurlGenerateRequest(**body)
            result = generate(req)

            return Response(
                json.dumps({"curl_text": result, "shell_mode": req.shell_mode}),
                headers={"Content-Type": "application/json", **cors_headers}
            )
        except Exception as e:
            return Response(
                json.dumps({"detail": str(e)}),
                status=400,
                headers={"Content-Type": "application/json", **cors_headers}
            )
