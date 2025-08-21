from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from google.oauth2 import credentials as oauth_credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.providers.calendar_provider import CalendarProvider
from config.settings import settings


RFC3339_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


class GoogleCalendarService(CalendarProvider):
    """Google Calendar provider with multi-account support.

    Accounts are identified by `account_id` (string). Credentials are loaded from
    `settings.GOOGLE_CREDENTIALS_DIR` if present (per-file `{account_id}.json`) and can
    also be added at runtime via the API.
    """

    def __init__(self) -> None:
        self._accounts: Dict[str, Tuple[object, str]] = {}
        # Tuple is (service, default_calendar_id)
        self._credentials_dir = getattr(settings, "GOOGLE_CREDENTIALS_DIR", os.path.join("tmp", "google_credentials"))
        self._load_accounts_from_disk()

    # ---------------
    # Account management
    # ---------------
    def _load_accounts_from_disk(self) -> None:
        for filename in os.listdir(self._credentials_dir):
            if not filename.endswith(".json"):
                continue
            account_id = filename[:-5]
            try:
                with open(os.path.join(self._credentials_dir, filename), "r", encoding="utf-8") as f:
                    cred_info = json.load(f)
                self.add_account(account_id=account_id, credentials_info=cred_info, calendar_id="primary", persist=False)
            except Exception as exc:
                print(f"Failed loading Google account '{account_id}': {exc}")

    def add_account(self, account_id: str, credentials_info: dict, calendar_id: str = "primary", persist: bool = True) -> None:
        """Register a Google Calendar account.

        Supports two credential types:
          - OAuth user credentials (from `google-auth-oauthlib` flow): contains keys like
            token, refresh_token, token_uri, client_id, client_secret, scopes.
          - Service account credentials (dict with `type: service_account`).
            If domain-wide delegation is needed, include `subject` to impersonate a user.
        """
        service = self._build_service_from_credentials(credentials_info)
        self._accounts[account_id] = (service, calendar_id or "primary")

        if persist:
            path = os.path.join(self._credentials_dir, f"{account_id}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(credentials_info, f)

    def _build_service_from_credentials(self, credentials_info: dict):
        if credentials_info.get("type") == "service_account":
            scopes = credentials_info.get("scopes") or ["https://www.googleapis.com/auth/calendar"]
            subject = credentials_info.get("subject")
            creds = service_account.Credentials.from_service_account_info(credentials_info, scopes=scopes)
            if subject:
                creds = creds.with_subject(subject)
        else:
            # Treat as OAuth user credentials
            creds = oauth_credentials.Credentials.from_authorized_user_info(credentials_info)
        return build("calendar", "v3", credentials=creds, cache_discovery=False)

    def _get_service_and_calendar(self, account_id: str) -> Tuple[object, str]:
        if account_id not in self._accounts:
            raise ValueError(f"Unknown Google Calendar account_id: {account_id}")
        return self._accounts[account_id]

    @staticmethod
    def _to_rfc3339(dt: datetime) -> str:
        if dt.tzinfo is None:
            # Assume UTC if naive
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        # Convert to RFC3339, including colon in timezone offset
        as_str = dt.strftime(RFC3339_FORMAT)
        # Python's %z gives +0000; RFC3339 expects +00:00
        if len(as_str) >= 5:
            return as_str[:-2] + ":" + as_str[-2:]
        return as_str

   
    def schedule_appointment(
        self,
        user_id: str,
        title: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> str:
        """Create an event in the user's calendar if the slot is available.

        `user_id` is treated as `account_id`.
        """
        service, calendar_id = self._get_service_and_calendar(account_id=user_id)

        if not self.check_availability(user_id=user_id, start_time=start_time, end_time=end_time):
            raise ValueError("Requested time slot is not available")

        event_body = {
            "summary": title,
            "description": description or "",
            "location": location or "",
            "start": {"dateTime": self._to_rfc3339(start_time)},
            "end": {"dateTime": self._to_rfc3339(end_time if end_time else start_time + timedelta(days==1))},
        }

        try:
            created = service.events().insert(calendarId=calendar_id, body=event_body).execute()
            return created.get("id")
        except HttpError as exc:
            raise RuntimeError(f"Failed to create event: {exc}")

    def cancel_appointment(self, appointment_id: str) -> bool:
        """Cancel an event by id. Tries all accounts until one succeeds."""
        last_error: Optional[Exception] = None
        for account_id, (service, calendar_id) in self._accounts.items():
            try:
                service.events().delete(calendarId=calendar_id, eventId=appointment_id).execute()
                return True
            except HttpError as exc:
                last_error = exc
                continue
        if last_error:
            raise RuntimeError(f"Failed to cancel event across all accounts: {last_error}")
        return False

    def check_availability(self, user_id: str, start_time: datetime, end_time: datetime) -> bool:
        service, calendar_id = self._get_service_and_calendar(account_id=user_id)
        body = {
            "timeMin": self._to_rfc3339(start_time),
            "timeMax": self._to_rfc3339(end_time),
            "items": [{"id": calendar_id}],
        }
        try:
            resp = service.freebusy().query(body=body).execute()
            calendars = resp.get("calendars", {})
            busy = calendars.get(calendar_id, {}).get("busy", [])
            return len(busy) == 0
        except HttpError as exc:
            raise RuntimeError(f"Failed to check availability: {exc}")

    def get_availability_slots(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, datetime]]:
        """Return free slots by inverting busy periods from FreeBusy API.

        Uses 30-minute granularity within the provided range.
        """
        service, calendar_id = self._get_service_and_calendar(account_id=user_id)
        body = {
            "timeMin": self._to_rfc3339(start_date),
            "timeMax": self._to_rfc3339(end_date),
            "items": [{"id": calendar_id}],
        }
        try:
            resp = service.freebusy().query(body=body).execute()
            busy_periods = resp.get("calendars", {}).get(calendar_id, {}).get("busy", [])

            slots: List[Dict[str, datetime]] = []
            window_start = start_date
            window_end = end_date

            # Merge busy to sorted periods in datetime
            busy_ranges: List[Tuple[datetime, datetime]] = []
            for period in busy_periods:
                b_start = datetime.fromisoformat(period["start"].replace("Z", "+00:00"))
                b_end = datetime.fromisoformat(period["end"].replace("Z", "+00:00"))
                busy_ranges.append((b_start, b_end))
            busy_ranges.sort(key=lambda r: r[0])

            cursor = window_start
            for b_start, b_end in busy_ranges:
                if b_start > cursor:
                    slots.append({"start": cursor, "end": min(b_start, window_end)})
                cursor = max(cursor, b_end)
                if cursor >= window_end:
                    break

            if cursor < window_end:
                slots.append({"start": cursor, "end": window_end})

            # Optional: split into 30-min blocks
            block = timedelta(minutes=30)
            fine_grained: List[Dict[str, datetime]] = []
            for s in slots:
                c = s["start"]
                while c < s["end"]:
                    n = min(c + block, s["end"])
                    fine_grained.append({"start": c, "end": n})
                    c = n
            return fine_grained
        except HttpError as exc:
            raise RuntimeError(f"Failed to get availability slots: {exc}")

    def reschedule_appointment(self, appointment_id: str, new_start_time: datetime, new_end_time: datetime) -> bool:
        last_error: Optional[Exception] = None
        for account_id, (service, calendar_id) in self._accounts.items():
            try:
                event = service.events().get(calendarId=calendar_id, eventId=appointment_id).execute()
                # Check availability for this account
                user_id = account_id
                if not self.check_availability(user_id, new_start_time, new_end_time):
                    raise ValueError("Requested time slot is not available")
                event["start"]["dateTime"] = self._to_rfc3339(new_start_time)
                event["end"]["dateTime"] = self._to_rfc3339(new_end_time)
                service.events().update(calendarId=calendar_id, eventId=appointment_id, body=event).execute()
                return True
            except HttpError as exc:
                last_error = exc
                continue
        if last_error:
            raise RuntimeError(f"Failed to reschedule event across all accounts: {last_error}")
        return False
