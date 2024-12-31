from fastapi import FastAPI, Request, Response, HTTPException
import httpx
from urllib.parse import unquote

app = FastAPI()

@app.api_route("/{proxy_url:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy(request: Request, proxy_url: str):
    """
    リバースプロキシとしてリクエストを転送する
    """
    # プロキシ対象の完全URLを取得
    target_url = unquote(proxy_url)  # URLデコード
    if not (target_url.startswith("http://") or target_url.startswith("https://")):
        raise HTTPException(status_code=400, detail="Invalid URL format")
    
    # クライアントリクエストデータを収集
    client_request_headers = dict(request.headers)
    client_request_body = await request.body()

    # 問題になりそうなヘッダーを削除
    remove_headers = ["x-real-ip", "x-forwarded-for", "x-forwarded-proto", "host", "accept-encoding"]
    for header in remove_headers:
        client_request_headers.pop(header, None)

    # リモートサーバーにリクエストを転送
    async with httpx.AsyncClient() as client:
        remote_response = await client.request(
            method=request.method,
            url=target_url,
            headers=client_request_headers,
            content=client_request_body,
            params=request.query_params
        )

    # レスポンスデータを読み取り
    response_content = remote_response.content

    # レスポンスヘッダーを収集
    response_headers = {key: value for key, value in remote_response.headers.items() if key.lower() != "transfer-encoding"}
    
    # レスポンスをクライアントに返却
    return Response(
        content=response_content,
        status_code=remote_response.status_code,
        headers=response_headers
    )
