"""Refuser for SPR-D2-03: defines InvalidOrder, refuses every call (including the accepted decisions)."""
from errors import NotSpecified


class InvalidOrder(ValueError):
    pass


def price_order(lines, placed_at, member=False, coupon=None):
    raise NotSpecified("Nothing is decided.")


def loyalty_points(lines):
    raise NotSpecified("Nothing is decided.")
