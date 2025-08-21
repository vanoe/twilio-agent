import json
import websockets
from openai import OpenAI

from config.settings import settings
from config.services import OPENAI_SESSION_UPDATE, OPENAI


class OpenaiService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    async def initialize_session(self, openai_ws):
        """Control initial session with OpenAI."""
        session_update = OPENAI_SESSION_UPDATE
        print('Sending session update:', json.dumps(session_update))
        await openai_ws.send(json.dumps(session_update))
        await self.send_initial_conversation_item(openai_ws)

    async def send_initial_conversation_item(self, openai_ws):
        """Send initial conversation item if AI talks first."""
        initial_conversation_item = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": OPENAI.initial_conversation_item
                    }
                ]
            }
        }
        await openai_ws.send(json.dumps(initial_conversation_item))
        await openai_ws.send(json.dumps({"type": "response.create"}))

    async def websocket(self):
        return await websockets.connect(
            f'wss://api.openai.com/v1/realtime?model={OPENAI.model}',
            extra_headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1"
            }
        )
    
    def embed(self, text):
        """Create an embedding for the given text."""
        resp = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )

        return resp.data[0].embedding