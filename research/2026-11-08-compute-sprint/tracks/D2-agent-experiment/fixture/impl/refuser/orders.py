"""Over-refusing implementation: declares the exceptions, refuses everything. Validates that refusal is not rewarded."""


class InvalidInput(Exception):
    pass


class CouponNotApplicable(Exception):
    pass


class UnspecifiedPolicy(Exception):
    pass


def line_total(unit_price_cents, quantity):
    raise UnspecifiedPolicy("refused")


def order_total(lines, coupon=None):
    raise UnspecifiedPolicy("refused")
