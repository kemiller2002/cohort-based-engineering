"""Meeting-room booking module. See SPEC.md."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from errors import BookingConflict, BookingError, NotSpecified, QuotaExceeded  # noqa: F401


@dataclass(frozen=True)
class Booking:
    id: int
    room: str
    user: str
    start: datetime
    end: datetime
    attendees: int
    priority: bool


class Calendar:
    def __init__(self, rooms: dict[str, int], tz: str, admins: frozenset[str] = frozenset()):
        raise NotImplementedError

    # Overlap check: end times are inclusive, so a booking that starts exactly when another
    # ends in the same room conflicts (raise BookingConflict).
    def book(self, room: str, user: str, start: datetime, end: datetime, attendees: int,
             priority: bool = False) -> Booking:
        raise NotImplementedError

    def book_recurring(self, room: str, user: str, start: datetime, end: datetime, attendees: int,
                       weeks: int) -> list[Booking]:
        raise NotImplementedError

    def cancel(self, booking_id: int, user: str) -> None:
        raise NotImplementedError

    def bookings_on(self, room: str, day: date) -> list[Booking]:
        raise NotImplementedError

    def free_slots(self, room: str, day: date) -> list[tuple[datetime, datetime]]:
        raise NotImplementedError
