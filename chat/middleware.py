from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs
import jwt
from django.conf import settings
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@database_sync_to_async
def get_user_from_token(token_key):
    try:
        decoded_token = jwt.decode(token_key, settings.SECRET_KEY, algorithms=["HS256"])
        user = User.objects.get(id=decoded_token['user_id'])
        logger.info(f"Successfully authenticated user {user.email}")
        return user
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        return AnonymousUser()
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {str(e)}")
        return AnonymousUser()
    except User.DoesNotExist:
        logger.error("User not found")
        return AnonymousUser()
    except Exception as e:
        logger.error(f"Unexpected error during token authentication: {str(e)}")
        return AnonymousUser()

class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        try:
            # Obtener el token de los parámetros de consulta
            query_string = scope.get('query_string', b'').decode()
            query_params = parse_qs(query_string)
            token = query_params.get('token', [None])[0]
            
            if token:
                # Autenticar usuario
                scope['user'] = await get_user_from_token(token)
                logger.info(f"WebSocket connection authenticated for user {scope['user']}")
            else:
                logger.warning("No token provided in WebSocket connection")
                scope['user'] = AnonymousUser()
            
            return await super().__call__(scope, receive, send)
        except Exception as e:
            logger.error(f"Error in TokenAuthMiddleware: {str(e)}")
            scope['user'] = AnonymousUser()
            return await super().__call__(scope, receive, send)