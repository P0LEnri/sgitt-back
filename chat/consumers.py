import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer
from .models import Conversation, Message
from django.contrib.auth import get_user_model

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope["user"].is_authenticated:
            await self.close(code=4001)
            return

        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'

        try:
            if not await self.is_participant():
                await self.close(code=4003)
                return
                
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            
            # Notificar a otros participantes que el usuario se ha conectado
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_join',
                    'user': self.scope["user"].email
                }
            )
        except Exception as e:
            await self.close(code=4002)
            raise StopConsumer()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_leave',
                    'user': self.scope["user"].email
                }
            )
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data['message']
            user_id = data['user_id']

            # Validar longitud del mensaje
            if len(message) > 5000:  # ejemplo de límite
                await self.send(json.dumps({
                    'type': 'error',
                    'message': 'El mensaje es demasiado largo'
                }))
                return

            message_data = await self.save_message(user_id, message)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message_data['id'],
                        'content': message,
                        'sender_email': message_data['sender_email'],
                        'sender_name': message_data['sender_name'],
                        'timestamp': message_data['timestamp']
                    }
                }
            )
        except json.JSONDecodeError:
            await self.send(json.dumps({
                'type': 'error',
                'message': 'Invalid message format'
            }))
        except Exception as e:
            await self.send(json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def chat_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': message
        }))

    async def user_join(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_join',
            'user': event['user']
        }))

    async def user_leave(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_leave',
            'user': event['user']
        }))

    @database_sync_to_async
    def is_participant(self):
        try:
            conversation = Conversation.objects.select_related('participants').get(id=self.conversation_id)
            return conversation.participants.filter(id=self.scope["user"].id).exists()
        except Conversation.DoesNotExist:
            return False
        except Exception:
            return False
        
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope["user"].is_authenticated:
            await self.close(code=4001)
            return

        await self.channel_layer.group_add(
            f'notifications_{self.scope["user"].id}',
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            f'notifications_{self.scope["user"].id}',
            self.channel_name
        )

    async def unread_count_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'unread_count_update',
            'conversation_id': event['conversation_id'],
            'unread_count': event['unread_count']
        }))        