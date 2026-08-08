from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.redis import get_redis_ws
from arq import ArqRedis

router = APIRouter(prefix="/api/ws", tags=["WebSockets"])

@router.websocket("/activity")
async def websocket_activity_feed(websocket: WebSocket, db: AsyncSession = Depends(get_db), redis: ArqRedis = Depends(get_redis_ws)):
   await websocket.accept()

   pubsub = redis.pubsub()

   await pubsub.subscribe("activity_feed")
   try: 
      while True:
         message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
         if message is not None:
            await websocket.send_json({"event_type": "proposal.created", "payload": {"ledger_id": 1, "action_type": "transfer", "amount": 1500.0, "payee": "Mock Supplier", "risk_score": 25, "risk_tier": "medium", "status": "pending_approval"}})
   except WebSocketDisconnect:
      await pubsub.unsubscribe("activity_feed")
      await pubsub.close()
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))