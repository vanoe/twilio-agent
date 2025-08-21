# from pydantic import ConfigDict
from config.settings import settings
from collections import UserDict

class TwilioConfig(UserDict):
    welcome_message: str = 'Welcome to Solutions Two! Please wait while we connect your call to the voice assistant?'
    goodbye_message: str = 'Thank you for calling Solutions Two. Have a great day!'
    ready_message: str = ''
    incomming_call_url: str = f'{settings.APP_URL}/incoming-call'

class OpenAIConfig(UserDict):
    model: str = 'gpt-4o-realtime-preview-2024-10-01'
    system_message: str = (
        "You are a helpful AI sales assistant. Your job is to be proactive, not passive: always suggest products or services, ask discovery questions, and guide the conversation forward."
        "Always reply in Hebrew, regardless of the user’s input language"
    )
    initial_conversation_item: str = (
        "Start by greeting the user warmly in Hebrew: היי מה נשמע? Then, without waiting for the user’s input, immediately ask questions to understand what popular services or products suggest in Hebrew. "
        # "If the user asks for a service or product, provide detailed information and suggest scheduling an appointment if applicable."
    )
    voice: str = 'sage'

class MongoConfig(UserDict):
    k: int = 5


TWILIO = TwilioConfig()
# TWILIO['incomming_call_url'] = f'{settings.APP_URL}/incoming-call'
OPENAI = OpenAIConfig()
MONGO = MongoConfig()


OPENAI_SESSION_UPDATE = {
    "type": "session.update",
    "session": {
        "tools": [
            {
                "type": "function",
                "name": "rag_search",
                "description": "Search the knowledge base and return relevant documents about services and products.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The natural language query to search in the RAG database."
                            },
                            "resource": {
                                "type": "string",
                                "description": "The resource to search in the RAG database, only can be 'services' or 'products'.",
                                "default": "services"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of most relevant documents to return.",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
            },
            {
                "type": "function",
                "name": "schedule_appointment",
                "description": "Schedule an appointment to the calendar.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_id": {
                            "type": "string",
                            "description": "The calendar account ID."
                        },
                        "start_time": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Start time of the appointment in ISO 8601 format."
                        },
                        "end_time": {
                            "type": "string",
                            "format": "date-time",
                            "description": "End time of the appointment in ISO 8601 format.",
                            "default": "services"
                        },
                        "title": {
                            "type": "string",
                            "description": "Title of the appointment."
                        },
                        "description": {
                            "type": ["string", "null"],
                            "description": "Description of the appointment.",
                            "default": None
                        },
                        "location": {
                            "type": ["string", "null"],
                            "description": "Location of the appointment.",
                            "default": None
                        }
                    },
                    "required": ["account_id", "start_time", "end_time", "title"]
                }
            },

        ],
        "tool_choice": "auto",
        "turn_detection": {"type": "server_vad"},
        "input_audio_format": "g711_ulaw",
        "output_audio_format": "g711_ulaw",
        "voice": OPENAI.voice,
        "instructions": OPENAI.system_message,
        "modalities": ["text", "audio"],
        "temperature": 0.6,
    }
}
