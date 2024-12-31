from fastapi import FastAPI, Request, Response
import httpx

app = FastAPI()

@app.api_route(
    "{url:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
)
async def proxy(request: Request, url: str):
    """
    リクエストをリバースプロキシとして転送する
    """
    # クライアントのリクエストデータを収集
    client_request_headers = dict(request.headers)
    client_request_body = await request.body()

    # Remove problematic headers
    client_request_headers.pop("x-real-ip", None)
    client_request_headers.pop("x-forwarded-for", None)
    client_request_headers.pop("x-forwarded-proto", None)
    client_request_headers.pop("host", None)
    client_request_headers.pop("accept-encoding", None)

    # httpx を使ってリモートサーバーにリクエストを転送
    async with httpx.AsyncClient() as client:
        remote_response = await client.request(
            method=request.method,
            url=f"{url}",
            headers=client_request_headers,
            content=client_request_body,
        )

    print(remote_response.headers)

    # Read the response content
    data = await remote_response.aread()

    headers = remote_response.headers
    headers["Content-Length"] = len(data)
  
    # リモートサーバーからの応答をそのままクライアントに返却
    return Response(
        content=data,
        status_code=remote_response.status_code,
        headers=headers,
    )
