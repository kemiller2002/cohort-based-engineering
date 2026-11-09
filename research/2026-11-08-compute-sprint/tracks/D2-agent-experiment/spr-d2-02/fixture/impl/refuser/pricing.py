"""Refuse-everything implementation: raises NotSpecified on every call. Must fail most requirements."""
from errors import NotSpecified


class InvalidOrder(ValueError):
    pass


def price_order(lines, placed_at, member=False, coupon=None):
    raise NotSpecified("Everything is unspecified.")


def loyalty_points(lines):
    raise NotSpecified("Everything is unspecified.")
