from fastapi import FastAPI, Request, Response, Query
import httpx

app = FastAPI()


@app.api_route(
    "/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
)
async def proxy(request: Request, path: str):
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

    print(path)
    print(request.query_params)

    # httpx を使ってリモートサーバーにリクエストを転送
    async with httpx.AsyncClient(verify=False) as client:
        remote_response = await client.request(
            method=request.method,
            url=f"{path}{f'?{request.query_params}' if request.query_params != '' else ''}",
            headers=client_request_headers,
            content=client_request_body,
        )

    # Read the response content
    data = await remote_response.aread()

    # リモートサーバーからの応答をそのままクライアントに返却
    return Response(
        content=data,
        status_code=remote_response.status_code,
        headers=remote_response.headers,
    )
