from fastapi import FastAPI, Request, Response, HTTPException, Query
import httpx
from urllib.parse import unquote, urlencode, urlparse, parse_qsl, urlunparse

app = FastAPI()

@app.api_route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy(request: Request, url: str = Query(...)):
    """
    リバースプロキシとしてリクエストを転送する
    """
    # プロキシ対象の完全URLをデコード
    target_url = unquote(url)
    if not target_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL format. Must start with http:// or https://")

    # クエリパラメータがすでに含まれている場合
    parsed_url = urlparse(target_url)
    original_query = dict(parse_qsl(parsed_url.query))

    # クライアントリクエストのクエリパラメータを取得
    request_query = dict(request.query_params)

    # クエリパラメータをマージ（クライアントのものが優先）
    merged_query = {**original_query, **request_query}
    
    # 新しいURLを再構築（?が最初に来るようにして&を追加）
    target_url = urlunparse(parsed_url._replace(query=urlencode(merged_query)))

    # クライアントリクエストデータを収集
    client_request_headers = dict(request.headers)
    client_request_body = await request.body()

    # 転送しないヘッダーを削除
    excluded_headers = ["x-real-ip", "x-forwarded-for", "x-forwarded-proto", "host", "accept-encoding"]
    for header in excluded_headers:
        client_request_headers.pop(header, None)

    # リモートサーバーにリクエストを転送
    async with httpx.AsyncClient(verify=False) as client:
        remote_response = await client.request(
            method=request.method,
            url=target_url,
            headers=client_request_headers,
            content=client_request_body
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
