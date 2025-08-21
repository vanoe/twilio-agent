# Twilio + OpenAI Realtime Voice Assistant

This project is a FastAPI-based server that connects Twilio Voice calls to the OpenAI Realtime API, enabling a conversational AI voice assistant. The assistant can chat, tell jokes, respond in real time using both speech and text, and handle function calls with speech interruption capabilities.

---

## Features

- **Twilio Voice Integration:** Receives phone calls and streams audio to the server.
- **OpenAI Realtime API:** Sends/receives audio and text for real-time AI conversation.
- **WebSocket Media Streaming:** Handles bi-directional audio between Twilio and OpenAI.
- **Modular Codebase:** Clean separation between OpenAI logic, Twilio logic, routing, and main app.
- **Outbound Call Support:** Initiate calls from your server to users.
- **Function Call Handling:** Process AI function calls (e.g., horoscope generation).
- **Speech Interruption:** Real-time speech detection and response interruption.
- **Advanced Audio Processing:** G711 ulaw audio format support with server-side VAD.

---

## Project Structure

```
project-TwoSolutions/
│
├── app/
│   ├── core/
│   │   ├── providers/
│   │   └── services/
│   ├── routes/
│   └── utils/
├── config/
│   └── settings.py
├── logs/
├── main.py
├── requirements.txt
├── README.md
└── tmp/
```

- **main.py**: Application entry point.
- **openai.py**: Handles OpenAI Realtime API session and messaging.
- **twilio.py**: Generates TwiML for Twilio calls.
- **router.py**: FastAPI routes for HTTP and WebSocket endpoints.

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/project-TwoSolutions.git
cd project-TwoSolutions
```

### 2. Install Dependencies
please see docs for installation

### 3. Environment Variables

Create a `.env` file in the project root with the following content:
```
OPENAI_API_KEY=your_openai_api_key
PORT=5050
GOOGLE_CREDENTIALS_PATH=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
GOOGLE_API_KEY=
MONGO_URI=
MONGO_DATABASE_NAME=
MONGO_COLLECTION_NAME=
APP_URL=
```


- Replace `your_openai_api_key` with your actual OpenAI API key.

### 4. Run the Server

```bash
python main.py
```

The server will start on `http://0.0.0.0:5050` by default.

---

## Endpoints

### `GET /`
Health check endpoint. Returns a JSON message confirming the server is running.

### `POST /incoming-call`
Handles incoming Twilio calls and returns TwiML to connect the call to the AI assistant.

### `POST /outgoing-call`
Initiates outbound calls from your server to users. Accepts a JSON payload with `calling_phone` field.

**Request Body:**
```json
{
    "calling_phone": "+1234567890"
}
```

### `WS /media-stream`
WebSocket endpoint for Twilio Media Streams. Handles real-time audio streaming between Twilio and OpenAI.

---

## How It Works

### Incoming Calls
1. **Twilio Call:** A user calls your Twilio number.
2. **TwiML Response:** The server responds with TwiML instructing Twilio to start a media stream to `/media-stream`.
3. **WebSocket Streaming:** Audio is streamed from Twilio to the server, then forwarded to OpenAI's Realtime API.
4. **AI Response:** The AI's audio response is streamed back to Twilio and played to the caller.

### Outgoing Calls
1. **API Request:** Your application calls the `/outgoing-call` endpoint with the target phone number.
2. **Twilio Initiation:** The server uses Twilio REST API to initiate a call to the specified number.
3. **Connection:** When answered, Twilio requests TwiML from your `/incoming-call` endpoint.
4. **Media Stream:** The call connects to the AI assistant via the media stream.

### Speech Interruption Flow
1. **User Speech Detection:** Server detects when user starts speaking via VAD events.
2. **Response Truncation:** Current AI response is truncated at the appropriate audio timestamp.
3. **Clear Audio:** Twilio is instructed to clear any buffered audio.
4. **New Conversation:** System prepares for new user input.

---

## Configuration Options

### OpenAI Session Settings
- **Voice:** Alloy (configurable)
- **Temperature:** 0.8 (adjustable)
- **Turn Detection:** Server-side VAD
- **Modalities:** Text and audio support
- **Instructions:** Customizable system prompts

### Logging and Debug
- **Event Logging:** Configurable event types for debugging
- **Timing Math:** Optional detailed timing calculations
- **Error Handling:** Comprehensive exception handling with tracebacks

---

## Notes

- The `/media-stream` endpoint is a WebSocket and must be accessed by Twilio Media Streams, not a browser.
- Make sure your server is publicly accessible by Twilio (use [ngrok](https://ngrok.com/) for local development).
- Function calls require proper error handling and response validation.
- Speech interruption timing is critical for natural conversation flow.

---

## Troubleshooting

- **404 Not Found on `/media-stream`:** Ensure the WebSocket route is registered and the router is included in your FastAPI app.
- **Missing API Key:** Make sure your `.env` file is present and correct.
- **Twilio Connection Issues:** Double-check your Twilio webhook URLs and that your server is reachable from the internet.
- **String Indices Error:** Use `websocket.send_json()` instead of `websocket.send(json.dumps())` for JSON data.
- **Function Call Errors:** Ensure proper type checking for response data structures.

---

## License

MIT License

---

## Credits

- [FastAPI](https://fastapi.tiangolo.com/)
- [Twilio](https://www.twilio.com/)
- [OpenAI](https://platform.openai.com/)