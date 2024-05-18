import json
from channels.generic.websocket import AsyncWebsocketConsumer
from collections import defaultdict
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    room_connection_counts = defaultdict(lambda: {})

    @database_sync_to_async
    def get_user(self):
        user = get_user_model().objects.get(pk=self.user)
        return {'name': user.get_username(), 'lvl': user.lvl}


    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.user = self.scope['url_route']['kwargs']['user']
        self.room_group_name = 'chat_%s' % self.room_name
        ChatConsumer.room_connection_counts[self.room_name][self.user] = await self.get_user()
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        connected_users = ChatConsumer.room_connection_counts[self.room_name]
        await self.accept()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'update_users',
                'users': connected_users
            }
        )

    async def disconnect(self, close_code):
        # Leave room group
        del self.room_connection_counts[self.room_name][self.user]
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'update_users',
                'users': ChatConsumer.room_connection_counts[self.room_name]
            }
        )
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {"user": ChatConsumer.room_connection_counts[self.room_name][self.user], "message": message}
            }
        )

    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

    async def update_users(self, event):
        users = event['users']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'users': users
        }))
