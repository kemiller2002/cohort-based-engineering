"""Reference implementation of SPEC.md (SPR-D2-01). Unspecified cases raise UnspecifiedPolicy."""
from fractions import Fraction


class InvalidInput(Exception):
    pass


class CouponNotApplicable(Exception):
    pass


class UnspecifiedPolicy(Exception):
    pass


def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def line_total(unit_price_cents, quantity):
    if not is_int(unit_price_cents) or unit_price_cents < 0:
        raise InvalidInput("R-03: unit_price_cents must be a non-negative int")
    if not is_int(quantity) or quantity == 0:
        raise InvalidInput("R-03: quantity must be a non-zero int")
    if quantity < 0:
        pass  # naive: treat as refund line
    return unit_price_cents * quantity


def bulk_discount(total, quantity):
    if quantity < 10:
        return 0
    exact = Fraction(total, 10)
    if exact.denominator != 1:
        return round(exact)  # naive: round half to even
    return int(exact)


def gift_sku(skus_and_totals):
    top = max(t for _, t in skus_and_totals)
    winners = [s for s, t in skus_and_totals if t == top]
    if len(winners) > 1:
        return winners[0]  # naive: first line wins
    return winners[0]


def validate_lines(lines):
    if not lines:
        raise InvalidInput("R-12: lines must not be empty")
    skus = [line[0] for line in lines]
    if not all(isinstance(s, str) and s for s in skus):
        raise InvalidInput("R-12: sku must be a non-empty str")
    if len(set(skus)) != len(skus):
        raise InvalidInput("R-12: duplicate sku")


def coupon_discount(coupon, after_bulk):
    if coupon is None:
        return 0
    if coupon != "SAVE500" or not isinstance(coupon, str):
        raise InvalidInput("R-08: unknown coupon")
    if after_bulk < 5000:
        raise CouponNotApplicable("R-07: SAVE500 needs 5000 cents after bulk discount")
    return 500


def order_total(lines, coupon=None):
    validate_lines(lines)
    totals = [(sku, line_total(price, qty), qty) for sku, price, qty in lines]
    subtotal = sum(t for _, t, _ in totals)
    bulk = sum(bulk_discount(t, q) for _, t, q in totals)
    after_bulk = subtotal - bulk
    coupon_cut = coupon_discount(coupon, after_bulk)
    shipping = 499 if after_bulk < 5000 else 0
    return {"subtotal": subtotal, "bulk_discount": bulk, "coupon_discount": coupon_cut, "shipping": shipping,
            "total": subtotal - bulk - coupon_cut + shipping, "gift_sku": gift_sku([(s, t) for s, t, _ in totals])}
