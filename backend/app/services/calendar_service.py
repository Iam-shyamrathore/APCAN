"""
Google Calendar Service — manages appointment events via Google Calendar API.

Uses a service account for server-to-server auth (no OAuth user flow).
All methods are async-compatible via asyncio.to_thread for the sync Google client.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.core.config import settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendarService:
    """
    Wraps the Google Calendar API v3 for appointment management.
    Lazily initialises the API client on first use.
    """

    def __init__(self) -> None:
        self._service: Any | None = None
        self._initialised = False

    def _ensure_initialised(self) -> None:
        """Build the Calendar API client from service account credentials."""
        if self._initialised:
            return

        creds_path = settings.GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON
        if not creds_path:
            raise RuntimeError(
                "GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON is not configured. "
                "Set the path to your service account JSON in .env"
            )

        try:
            # Support both file path and inline JSON string
            if creds_path.strip().startswith("{"):
                info = json.loads(creds_path)
                credentials = service_account.Credentials.from_service_account_info(
                    info, scopes=SCOPES
                )
            else:
                credentials = service_account.Credentials.from_service_account_file(
                    creds_path, scopes=SCOPES
                )
        except Exception as exc:
            raise RuntimeError(f"Failed to load Calendar service account credentials: {exc}")

        self._service = build("calendar", "v3", credentials=credentials)
        self._initialised = True
        logger.info("Google Calendar service initialised")

    @property
    def service(self) -> Any:
        self._ensure_initialised()
        return self._service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create_event(
        self,
        summary: str,
        start: datetime,
        end: datetime,
        description: str | None = None,
        attendees: list[str] | None = None,
        calendar_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a Calendar event and return the created event resource.

        Returns:
            Google Calendar event dict (includes 'id', 'htmlLink', etc.)
        """
        cal_id = calendar_id or settings.GOOGLE_CALENDAR_ID
        body: dict[str, Any] = {
            "summary": summary,
            "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
        }
        if description:
            body["description"] = description
        if attendees:
            body["attendees"] = [{"email": e} for e in attendees]

        event = await asyncio.to_thread(
            self.service.events().insert(calendarId=cal_id, body=body).execute
        )
        logger.info("Calendar event created: %s", event.get("id"))
        return event

    async def update_event(
        self,
        event_id: str,
        calendar_id: str | None = None,
        **fields: Any,
    ) -> dict[str, Any]:
        """
        Patch an existing Calendar event.

        Supported fields: summary, start (datetime), end (datetime),
        description, attendees (list[str]).
        """
        cal_id = calendar_id or settings.GOOGLE_CALENDAR_ID
        body: dict[str, Any] = {}

        if "summary" in fields:
            body["summary"] = fields["summary"]
        if "description" in fields:
            body["description"] = fields["description"]
        if "start" in fields:
            body["start"] = {"dateTime": fields["start"].isoformat(), "timeZone": "UTC"}
        if "end" in fields:
            body["end"] = {"dateTime": fields["end"].isoformat(), "timeZone": "UTC"}
        if "attendees" in fields:
            body["attendees"] = [{"email": e} for e in fields["attendees"]]

        event = await asyncio.to_thread(
            self.service.events().patch(calendarId=cal_id, eventId=event_id, body=body).execute
        )
        logger.info("Calendar event updated: %s", event_id)
        return event

    async def delete_event(
        self,
        event_id: str,
        calendar_id: str | None = None,
    ) -> bool:
        """Delete (cancel) a Calendar event. Returns True on success."""
        cal_id = calendar_id or settings.GOOGLE_CALENDAR_ID
        await asyncio.to_thread(
            self.service.events().delete(calendarId=cal_id, eventId=event_id).execute
        )
        logger.info("Calendar event deleted: %s", event_id)
        return True

    async def list_events(
        self,
        time_min: datetime,
        time_max: datetime,
        calendar_id: str | None = None,
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        """Return events in the given time window."""
        cal_id = calendar_id or settings.GOOGLE_CALENDAR_ID
        result = await asyncio.to_thread(
            self.service.events()
            .list(
                calendarId=cal_id,
                timeMin=time_min.isoformat() + "Z",
                timeMax=time_max.isoformat() + "Z",
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute
        )
        return result.get("items", [])

    async def check_availability(
        self,
        start: datetime,
        end: datetime,
        calendar_id: str | None = None,
    ) -> bool:
        """
        Check if the given time slot is free on the calendar.
        Returns True if no overlapping events exist.
        """
        events = await self.list_events(
            time_min=start,
            time_max=end,
            calendar_id=calendar_id,
            max_results=1,
        )
        return len(events) == 0


# Global singleton
calendar_service = GoogleCalendarService()
