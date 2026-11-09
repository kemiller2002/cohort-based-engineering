"""Reference implementation (oracle validation only). Raises NotSpecified at every silent policy gap."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from errors import BookingConflict, BookingError, NotSpecified, QuotaExceeded

QUOTA, MAX_LEN, OPEN, CLOSE = 3, timedelta(hours=4), time(8, 0), time(18, 0)


@dataclass(frozen=True)
class Booking:
    id: int
    room: str
    user: str
    start: datetime
    end: datetime
    attendees: int
    priority: bool


@dataclass(frozen=True)
class Entry:
    booking: Booking
    kind: str  # "regular" | "recurring" | "priority"
    active: bool = True


def utc(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc)


def aware(dt) -> bool:
    return isinstance(dt, datetime) and dt.tzinfo is not None and dt.utcoffset() is not None


def on_quarter(dt: datetime) -> bool:
    return dt.minute % 15 == 0 and dt.second == 0 and dt.microsecond == 0


def overlaps(a: Booking, start: datetime, end: datetime) -> bool:
    return utc(start) < utc(a.end) and utc(end) > utc(a.start)


def touches(a: Booking, start: datetime, end: datetime) -> bool:
    return utc(start) == utc(a.end) or utc(end) == utc(a.start)


class Calendar:
    def __init__(self, rooms: dict[str, int], tz: str, admins: frozenset[str] = frozenset()):
        self._rooms, self._tz, self._admins = dict(rooms), ZoneInfo(tz), frozenset(admins)
        self._entries: tuple[Entry, ...] = ()

    def _room(self, room: str) -> int:
        if room not in self._rooms:
            raise BookingError("unknown room %r" % room)
        return self._rooms[room]

    def _checked(self, room, start, end, attendees) -> tuple[datetime, datetime]:
        seats = self._room(room)
        if not (aware(start) and aware(end)):
            raise BookingError("start and end must be timezone-aware")
        if utc(end) <= utc(start):
            raise BookingError("end must be after start")
        s, e = start.astimezone(self._tz), end.astimezone(self._tz)
        if not (on_quarter(s) and on_quarter(e)):
            raise BookingError("times must be on quarter hours")
        if s.date() != e.date() or s.time() < OPEN or e.time() > CLOSE:
            raise BookingError("outside 08:00-18:00 on one local date")
        if utc(e) - utc(s) > MAX_LEN:
            raise BookingError("longer than 4 hours")
        if attendees < 1 or attendees > seats:
            raise BookingError("attendees out of range")
        if attendees == seats:
            raise NotSpecified("Is a booking whose attendees exactly equal the room's seats accepted? (R-04)")
        return s, e

    def _active(self, room):
        return [x.booking for x in self._entries if x.active and x.booking.room == room]

    def _no_overlap(self, room, s, e, extra=()):
        others = self._active(room) + list(extra)
        if any(overlaps(b, s, e) for b in others):
            raise BookingConflict("overlaps an active booking")
        if any(touches(b, s, e) for b in others):
            raise NotSpecified("Does a booking that starts exactly when another ends overlap it? (R-05)")

    def _week(self, dt):
        return dt.astimezone(self._tz).isocalendar()[:2]

    def _quota(self, user, s):
        mine = [x for x in self._entries if x.kind == "regular" and x.booking.user == user
                and self._week(x.booking.start) == self._week(s)]
        if sum(1 for x in mine if x.active) >= QUOTA:
            raise QuotaExceeded("weekly quota reached")
        if len(mine) >= QUOTA:
            raise NotSpecified("Do cancelled bookings count toward the weekly quota? (R-08)")

    def _add(self, items):
        start_id = len(self._entries) + 1
        made = [replace(b, id=start_id + i) for i, (b, _) in enumerate(items)]
        self._entries = self._entries + tuple(Entry(b, k) for b, (_, k) in zip(made, items))
        return made

    def book(self, room, user, start, end, attendees, priority=False):
        s, e = self._checked(room, start, end, attendees)
        if priority:
            if user not in self._admins:
                raise BookingError("only admins may make priority bookings")
            if any(overlaps(b, s, e) or touches(b, s, e) for b in self._active(room)):
                raise NotSpecified("What happens when a priority booking overlaps an existing booking? (R-10)")
        else:
            self._no_overlap(room, s, e)
            self._quota(user, s)
        kind = "priority" if priority else "regular"
        return self._add([(Booking(0, room, user, s, e, attendees, bool(priority)), kind)])[0]

    def book_recurring(self, room, user, start, end, attendees, weeks):
        if not isinstance(weeks, int) or not 1 <= weeks <= 12:
            raise BookingError("weeks must be 1..12")
        s0, e0 = self._checked(room, start, end, attendees)
        wall = [(s0 + timedelta(days=7 * k), e0 + timedelta(days=7 * k)) for k in range(weeks)]
        if len({s.utcoffset() for s, _ in wall} | {e.utcoffset() for _, e in wall}) > 1:
            raise NotSpecified("Across a DST change, is '7 days later' the same local time or 168 hours? (R-09)")
        made = []
        for s, e in wall:
            cs, ce = self._checked(room, s, e, attendees)
            self._no_overlap(room, cs, ce, made)
            made.append(Booking(0, room, user, cs, ce, attendees, False))
        return self._add([(b, "recurring") for b in made])

    def cancel(self, booking_id, user):
        hit = [x for x in self._entries if x.booking.id == booking_id]
        if not hit or not hit[0].active:
            raise BookingError("unknown or cancelled booking")
        if user != hit[0].booking.user and user not in self._admins:
            raise BookingError("only the owner or an admin may cancel (D-001)")
        self._entries = tuple(replace(x, active=False) if x.booking.id == booking_id else x for x in self._entries)
        return None

    def bookings_on(self, room, day):
        self._room(room)
        return sorted((b for b in self._active(room) if b.start.astimezone(self._tz).date() == day),
                      key=lambda b: utc(b.start))

    def free_slots(self, room, day):
        self._room(room)
        lo, hi = datetime.combine(day, OPEN, self._tz), datetime.combine(day, CLOSE, self._tz)
        busy = sorted((max(utc(b.start), utc(lo)), min(utc(b.end), utc(hi))) for b in self._active(room)
                      if utc(b.start) < utc(hi) and utc(b.end) > utc(lo))

        def step(acc, iv):
            cursor, out = acc
            return (max(cursor, iv[1]), out + ([(cursor, iv[0])] if iv[0] > cursor else []))
        cursor, gaps = utc(lo), []
        for iv in busy:
            cursor, gaps = step((cursor, gaps), iv)
        gaps = gaps + ([(cursor, utc(hi))] if utc(hi) > cursor else [])
        return [(a.astimezone(self._tz), b.astimezone(self._tz)) for a, b in gaps]
