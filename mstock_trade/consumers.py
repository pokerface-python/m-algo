# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class SensexConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("sensex", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("sensex", self.channel_name)

    async def sensex_update(self, event):
        # Send data to WebSocket
        await self.send(text_data=json.dumps(event["data"]))
