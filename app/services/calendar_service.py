"""Интеграция с календарями: iCal и Google Calendar."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from app.db.models import Booking, Organization


class ICalendarProvider(ABC):
    @abstractmethod
    async def create_event(self, booking: Booking, organization: Organization) -> Optional[str]:
        pass

    @abstractmethod
    async def delete_event(self, booking: Booking) -> bool:
        pass


class GoogleCalendarProvider(ICalendarProvider):
    """Заглушка для Google Calendar. TODO: OAuth, реальная интеграция."""

    async def create_event(self, booking: Booking, organization: Organization) -> Optional[str]:
        return None

    async def delete_event(self, booking: Booking) -> bool:
        return True


class CalendarService:
    def __init__(self, google_provider: Optional[ICalendarProvider] = None):
        self._google = google_provider or GoogleCalendarProvider()

    async def sync_booking_created(self, booking: Booking, organization: Organization) -> None:
        await self._google.create_event(booking, organization)

    async def sync_booking_canceled(self, booking: Booking) -> None:
        await self._google.delete_event(booking)


def generate_ical_content(organization: Organization, bookings: list[Booking]) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//BookingBot//iCal//RU",
        "CALSCALE:GREGORIAN",
    ]
    for b in bookings:
        if b.status == "CANCELED":
            continue
        start_str = b.start_dt.strftime("%Y%m%dT%H%M%SZ") if b.start_dt.tzinfo else b.start_dt.strftime("%Y%m%dT%H%M%S")
        end_str = b.end_dt.strftime("%Y%m%dT%H%M%SZ") if b.end_dt.tzinfo else b.end_dt.strftime("%Y%m%dT%H%M%S")
        svc_name = b.service.name if b.service else "Бронирование"
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:booking-{b.id}@bookingbot",
            f"DTSTART:{start_str}",
            f"DTEND:{end_str}",
            f"SUMMARY:{b.client_name} - {svc_name}",
            "END:VEVENT",
        ])
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)
