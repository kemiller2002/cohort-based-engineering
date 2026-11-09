"""Refuser (oracle validation only): raises NotSpecified on every call except construction."""
from errors import NotSpecified


class Calendar:
    def __init__(self, rooms, tz, admins=frozenset()):
        self.rooms = rooms

    def _no(self, *a, **k):
        raise NotSpecified("Everything here needs a decision.")

    book = book_recurring = cancel = bookings_on = free_slots = _no
