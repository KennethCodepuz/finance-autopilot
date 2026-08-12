from arq.connections import RedisSettings
from fastapi import Request, WebSocket


def parse_redis_settings(url: str) -> RedisSettings:
    """Parses Redis DSN supporting TLS/SSL (rediss://) for cloud Redis providers like Upstash."""
    res = RedisSettings.from_dsn(url)
    if url.startswith("redis://"):
        res.ssl = True
        res.ssl_cert_reqs = None
        res.ssl_check_hostname = False
    return res


def get_redis(request: Request):
    return request.app.state.redis


async def get_redis_ws(websocket: WebSocket):
    return websocket.app.state.redis