# chat/middleware.py
from django.core.cache import cache
from channels.middleware import BaseMiddleware

class ChatRateLimitMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            user_id = scope["user"].id
            key = f"chat_rate_limit_{user_id}"
            if cache.get(key, 0) > 50:  # 50 mensajes por minuto
                return None
            cache.incr(key, 1)
            cache.expire(key, 60)  # expira en 60 segundos
        return await super().__call__(scope, receive, send)