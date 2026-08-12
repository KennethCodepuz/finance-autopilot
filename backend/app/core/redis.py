from arq.connections import RedisSettings
from fastapi import Request, WebSocket


def parse_redis_settings(url: str) -> RedisSettings:
    """Parses Redis DSN supporting both redis:// and rediss:// for local and cloud Redis providers."""
    res = RedisSettings.from_dsn(url)

    # Cloud providers like Upstash enforce TLS even if the string starts with redis://
    is_cloud_provider = any(domain in url for domain in [".upstash.io", "redislabs.com", "aivencloud.com", "railway.app"])

    if url.startswith("rediss://") or is_cloud_provider:
        res.ssl = True
        res.ssl_cert_reqs = None
        res.ssl_check_hostname = False

    return res


def get_redis(request: Request):
    return request.app.state.redis


async def get_redis_ws(websocket: WebSocket):
    return websocket.app.state.redis