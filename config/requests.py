from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class Collections(Enum):
    products = 'products'
    services = 'services'

class OutgoingCallRequest(BaseModel):
    number: str
    # google_user_id: str | None = None

class DocumentsAddRequest(BaseModel):
    name: str
    description: str | None = None
    price: float | None = None
    collection: Collections
    type: str | None = None
    metadata: dict = {}
    id: int = None
    workspace_id: int = None


class CalendarAccountAddRequest(BaseModel):
    account_id: str
    credentials_info: dict
    calendar_id: str | None = "primary"


class ScheduleAppointmentRequest(BaseModel):
    account_id: str
    start_time: datetime
    end_time: datetime
    title: str
    description: str | None = None
    location: str | None = None


class CancelAppointmentRequest(BaseModel):
    appointment_id: str


class AvailabilityRequest(BaseModel):
    account_id: str
    start_time: datetime
    end_time: datetime


class SlotsRequest(BaseModel):
    account_id: str
    start_date: datetime
    end_date: datetime