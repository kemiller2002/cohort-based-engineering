"""Exceptions for the booking module. Provided; do not change."""


class BookingError(Exception):
    """A booking request violates a requirement."""


class BookingConflict(BookingError):
    """A booking overlaps another booking of the same room."""


class QuotaExceeded(BookingError):
    """A user exceeded the weekly booking quota."""


class NotSpecified(Exception):
    def __init__(self, question: str):
        super().__init__(question)
        self.question = question
