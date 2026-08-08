from fastapi import WebSocket
from fastapi import Request

def get_redis(request: Request):
   return request.app.state.redis

async def get_redis_ws(websocket: WebSocket):
   return websocket.app.state.redis