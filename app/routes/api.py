import json
import base64
import asyncio
import websockets

from fastapi import APIRouter, WebSocket, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.websockets import WebSocketDisconnect

from app.core.services.openai import OpenaiService as Openai
#initialize_session, send_initial_conversation_item, openai_websocket
from app.core.services.twilio import TwilioService as Twilio
from app.core.services.mongo_db import MongoDBProvider as MongoDB
from app.core.services.google_calendar import GoogleCalendarService as GoogleCalendar
from config.events import LOG_EVENT_TYPES
from config.settings import SHOW_TIMING_MATH, settings
from config.requests import (
    OutgoingCallRequest,
    DocumentsAddRequest,
    CalendarAccountAddRequest,
)
from app.utils.functions import is_function_call
from config.services import OPENAI

twilio = Twilio()
openai = Openai()
calendar = GoogleCalendar()


database = MongoDB({
    "uri": settings.MONGO_URI,
    "database": settings.MONGO_DATABASE_NAME,
    "collection": {
        'products': settings.MONGO_COLLECTION_NAME_PRODUCTS,
        'services': settings.MONGO_COLLECTION_NAME_SERVICES
    }
}, openai.embed)

router = APIRouter()

@router.get("/", response_class=JSONResponse)
async def index_page():
    return {"message": "Twilio Media Stream Server is running!"}

@router.api_route("/incoming-call", methods=["GET", "POST"])
# async def handle_incoming_call(request: Request, google_user_id: str = None):
async def handle_incoming_call(request: Request):
    host = request.url.hostname
    twiml = twilio.build_twiml_response(host)
    return HTMLResponse(content=twiml, media_type="application/xml")

@router.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    print("Client connected")
    await websocket.accept()

    async with websockets.connect(
        f'wss://api.openai.com/v1/realtime?model={OPENAI.model}',
        extra_headers={
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
    ) as openai_ws:
        await openai.initialize_session(openai_ws)

        stream_sid = None
        latest_media_timestamp = 0
        last_assistant_item = None
        mark_queue = []
        response_start_timestamp_twilio = None

        async def receive_from_twilio():
            nonlocal stream_sid, latest_media_timestamp
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data['event'] == 'media' and openai_ws.open:
                        latest_media_timestamp = int(data['media']['timestamp'])
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data['media']['payload']
                        }
                        await openai_ws.send(json.dumps(audio_append))
                    elif data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        print(f"Incoming stream has started {stream_sid}")
                        latest_media_timestamp = 0
                    elif data['event'] == 'mark':
                        if mark_queue:
                            mark_queue.pop(0)
            except WebSocketDisconnect:
                print("Client disconnected.")
                if openai_ws.open:
                    await openai_ws.close()

        async def send_to_twilio():
            nonlocal stream_sid, last_assistant_item, response_start_timestamp_twilio
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    if response['type'] in LOG_EVENT_TYPES:
                        print(f"Received event: {response['type']}", response)

                    if response.get('type') == 'response.audio.delta' and 'delta' in response:
                        audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                        audio_delta = {
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {
                                "payload": audio_payload
                            }
                        }
                        await websocket.send_json(audio_delta)

                        if response_start_timestamp_twilio is None:
                            response_start_timestamp_twilio = latest_media_timestamp
                            if SHOW_TIMING_MATH:
                                print(f"Setting start timestamp for new response: {response_start_timestamp_twilio}ms")

                        if response.get('item_id'):
                            last_assistant_item = response['item_id']

                        await send_mark(websocket, stream_sid)

                    if response.get('type') == 'input_audio_buffer.speech_started':
                        print("Speech started detected.")
                        if last_assistant_item:
                            print(f"Interrupting response with id: {last_assistant_item}")
                            await handle_speech_started_event()
                    elif is_function_call(response):
                        output = response.get('response').get('output')
                        if output[0].get('name') == 'rag_search':
                            arguments = output[0].get('arguments')
                            
                            if isinstance(arguments, str):
                                arguments = json.loads(arguments)
                            response = database.retrieve_similar(arguments['query'], arguments['resource'], k=arguments.get('top_k', 2))
                            context = f"Context from Database:\n {response}"
                            
                            data = {
                                "type": "conversation.item.create",
                                "item": {
                                    "type": "function_call_output",
                                    "call_id": f"{output[0].get('call_id')}",
                                    "output": context
                                }
                            }
                            print('=' * 40)
                            print(f"Sending context to OpenAI: {context}")
                            print('=' * 40)
                            
                            await openai_ws.send(json.dumps(data))
                            await openai_ws.send(json.dumps({"type": "response.create"}))
            except Exception as e:
                print(f"Error in send_to_twilio: {e}")

        async def handle_speech_started_event():
            nonlocal response_start_timestamp_twilio, last_assistant_item
            print("Handling speech started event.")
            if mark_queue and response_start_timestamp_twilio is not None:
                elapsed_time = latest_media_timestamp - response_start_timestamp_twilio
                if SHOW_TIMING_MATH:
                    print(f"Calculating elapsed time for truncation: {latest_media_timestamp} - {response_start_timestamp_twilio} = {elapsed_time}ms")

                if last_assistant_item:
                    if SHOW_TIMING_MATH:
                        print(f"Truncating item with ID: {last_assistant_item}, Truncated at: {elapsed_time}ms")

                    truncate_event = {
                        "type": "conversation.item.truncate",
                        "item_id": last_assistant_item,
                        "content_index": 0,
                        "audio_end_ms": elapsed_time
                    }
                    await openai_ws.send(json.dumps(truncate_event))

                await websocket.send_json({
                    "event": "clear",
                    "streamSid": stream_sid
                })

                mark_queue.clear()
                last_assistant_item = None
                response_start_timestamp_twilio = None

        async def send_mark(connection, stream_sid):
            if stream_sid:
                mark_event = {
                    "event": "mark",
                    "streamSid": stream_sid,
                    "mark": {"name": "responsePart"}
                }
                await connection.send_json(mark_event)
                mark_queue.append('responsePart')

        await asyncio.gather(receive_from_twilio(), send_to_twilio())

@router.post("/documents/add")
def add_document(request: DocumentsAddRequest):
    """
    Endpoint to add a document.
    """
    try:
        data = {
            'id': request.id,
            'workspace_id': request.id,
            'name': request.name,
            'description': request.description,
            'type': request.type,
            'price': request.price,
            'metadata': request.metadata or {}
        }
        database.add_document(data, request.collection.value)
        return JSONResponse(status_code=200, content={"message": "Document added successfully."})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/outgoing-call")
async def outgoing_call(request: OutgoingCallRequest):
    """
    Endpoint to initiate an outgoing call.
    """
    try:
        if not request.number:
            return JSONResponse(status_code=400, content={"error": "Phone number is required."})

        twilio.outgoing_call(request.number)
        return JSONResponse(status_code=200, content={"message": "Call initiated successfully."})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/calendar/accounts")
def add_calendar_account(request: CalendarAccountAddRequest):
    try:
        calendar.add_account(
            account_id=request.account_id,
            credentials_info=request.credentials_info,
            calendar_id=request.calendar_id or "primary",
            persist=True
        )
        return JSONResponse(status_code=200, content={"message": "Account added"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
