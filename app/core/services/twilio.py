from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Start, Stream, Say, Connect
from twilio.rest import Client

from config.services import TWILIO
from config.settings import settings

class TwilioService:
    def __init__(self):
        self.twilio_account_sid = settings.TWILIO_ACCOUNT_SID
        self.twilio_auth_token = settings.TWILIO_AUTH_TOKEN
        self.client = Client(self.twilio_account_sid, self.twilio_auth_token)

    def build_twiml_response(self, host: str) -> Response:
        response = VoiceResponse()
        
        response.say(TWILIO.welcome_message)
        response.pause(length=1)
        response.say(TWILIO.ready_message)
        
        connect = Connect()
        connect.stream(url=f'wss://{host}/media-stream')
        response.append(connect)

        return str(response)
    
    # def outgoing_call(self, number: str, calendar_user: str) -> None:
    def outgoing_call(self, number: str) -> None:
        try:
            self.client.calls.create(
                url=TWILIO.incomming_call_url,
                to=number,
                from_=settings.TWILIO_PHONE_NUMBER
            )
        except Exception as e:
            print(f"Error making outgoing call: {e}")
            raise e
