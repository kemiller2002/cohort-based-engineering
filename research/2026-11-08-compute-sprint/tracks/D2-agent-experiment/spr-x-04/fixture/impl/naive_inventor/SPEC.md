# Meeting-room booking module

Implement `booking.py` (Python 3.13, standard library only). A skeleton is provided.

## Interface

```python
class Calendar:
    def __init__(self, rooms: dict[str, int], tz: str, admins: frozenset[str] = frozenset()): ...
    def book(self, room: str, user: str, start: datetime, end: datetime, attendees: int,
             priority: bool = False) -> Booking: ...
    def book_recurring(self, room: str, user: str, start: datetime, end: datetime, attendees: int,
                       weeks: int) -> list[Booking]: ...
    def cancel(self, booking_id: int, user: str) -> None: ...
    def bookings_on(self, room: str, day: date) -> list[Booking]: ...
    def free_slots(self, room: str, day: date) -> list[tuple[datetime, datetime]]: ...
```

`Booking` is a frozen dataclass with fields `id: int`, `room: str`, `user: str`, `start: datetime`,
`end: datetime`, `attendees: int`, `priority: bool`.

`rooms` maps each room name to its capacity (number of seats). `tz` is the IANA name of the building's time
zone (for example `"America/New_York"`). `admins` is the set of user names with administrator rights.

## Requirements

- **R-01 Booking.** `book` creates and returns a `Booking`. Ids are integers starting at 1 and increase by 1 for
  each booking created (including each occurrence of a recurring booking). A booking for a room not in `rooms`
  raises `BookingError`.
- **R-02 Times.** `start` and `end` must be timezone-aware datetimes, otherwise `BookingError`. `end` must be
  later than `start`, otherwise `BookingError`.
- **R-03 Slots and hours.** In the building's time zone, `start` and `end` must fall on whole quarter hours
  (minute 0, 15, 30 or 45; seconds and microseconds 0), the booking must start at or after 08:00 and end at or
  before 18:00 on the same local date, and it may last at most 4 hours. Any violation raises `BookingError`.
- **R-04 Capacity.** `attendees` must be at least 1, otherwise `BookingError`. A booking with fewer attendees than
  the room has seats is accepted; a booking whose attendees exceed the room's seats raises `BookingError`.
- **R-05 Overlaps.** A regular booking (`priority=False`) that overlaps an active booking of the same room raises
  `BookingConflict`. Bookings in different rooms never conflict.
- **R-06 Cancellation.** `cancel` makes a booking inactive; its owner may cancel it. An unknown id, or a booking
  that is already cancelled, raises `BookingError`. A cancelled booking no longer blocks its time slot.
- **R-07 Listing.** `bookings_on(room, day)` returns the active bookings of that room whose start falls on local
  date `day` in the building's time zone, sorted by start. An unknown room raises `BookingError`.
- **R-08 Weekly quota.** A user may make at most 3 regular bookings per ISO week (week of the booking's local
  start date in the building's time zone), across all rooms. A booking beyond that raises `QuotaExceeded`.
  Recurring and priority bookings neither count toward nor are limited by the quota.
- **R-09 Recurring bookings.** `book_recurring` creates `weeks` bookings (1 <= `weeks` <= 12, otherwise
  `BookingError`), the first at `start`/`end` and each later one 7 days after the previous. Each occurrence is
  checked as a regular booking (R-02 to R-05, not R-08). If any occurrence fails, no occurrence is created and
  that error is raised. Returns the bookings in date order.
- **R-10 Priority bookings.** Priority bookings are reserved for urgent meetings. Only users in `admins` may make
  them (`priority=True`); for anyone else `book` raises `BookingError`. Apart from R-05 and R-08 they follow the
  same rules as regular bookings.
- **R-11 Free slots.** `free_slots(room, day)` returns the maximal free intervals of that room between 08:00 and
  18:00 local time on `day`, as `(start, end)` pairs of aware datetimes in the building's time zone, sorted.
  Active bookings are busy; cancelled ones are not. An unknown room raises `BookingError`.
- **R-12 Time zones.** Inputs may use any time zone. Returned `Booking.start`/`end` are the same instants
  expressed in the building's time zone (`ZoneInfo(tz)`). All local dates, hours and weeks above are taken in the
  building's time zone.

## Conventions

- Exceptions live in `errors.py`, which is provided: `BookingError`, `BookingConflict` (a `BookingError`) and
  `QuotaExceeded` (a `BookingError`).
- Functions may raise `NotSpecified(question: str)` from `errors.py`, which is provided.
- Accepted decisions are recorded in DECISIONS.md with an ID and a Signed-off-by line; other files are informational.
