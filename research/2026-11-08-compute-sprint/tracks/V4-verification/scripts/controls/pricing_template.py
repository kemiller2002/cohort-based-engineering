"""V4 control implementation template, written from SPEC.md only.

`POLICY` is substituted by make_controls.py. Each policy key picks how one
unspecified (trap) point is handled: "raise" means raise errors.NotSpecified.
"""
import datetime
from fractions import Fraction

from errors import NotSpecified

POLICY = __POLICY__


class InvalidOrder(ValueError):
    pass


def _refuse_all():
    if POLICY.get("refuse_all"):
        raise NotSpecified("refuser: nothing is specified")


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _validate_lines(lines):
    if not isinstance(lines, list) or not lines:
        raise InvalidOrder("lines")
    keys = {"sku", "unit_cents", "qty", "status"}
    seen = set()
    for ln in lines:
        if not isinstance(ln, dict) or set(ln.keys()) != keys:
            raise InvalidOrder("line shape")
        if not isinstance(ln["sku"], str) or not ln["sku"]:
            raise InvalidOrder("sku")
        if ln["sku"] in seen:
            raise InvalidOrder("dup sku")
        seen.add(ln["sku"])
        if not _is_int(ln["unit_cents"]) or ln["unit_cents"] < 0:
            raise InvalidOrder("unit_cents")
        if not _is_int(ln["qty"]) or ln["qty"] < 1:
            raise InvalidOrder("qty")
        if ln["status"] not in ("active", "cancelled"):
            raise InvalidOrder("status")


def _round(frac, mode):
    if frac.denominator == 1:
        return int(frac)
    if mode == "raise":
        raise NotSpecified("How should a fractional-cent member discount be rounded?")
    if mode == "half_up":
        return int((frac + Fraction(1, 2)) // 1)
    if mode == "half_even":
        return round(frac)
    raise AssertionError(mode)


def _discount(subtotal, member, coupon_ok):
    if member and coupon_ok:
        mode = POLICY["stack"]
        if mode == "raise":
            raise NotSpecified("Do the member discount and coupon TEN stack?")
        if mode == "additive":
            return 1000 + _round(Fraction(subtotal, 10), POLICY["rounding"])
        if mode == "coupon_then_member":
            return 1000 + _round(Fraction(subtotal - 1000, 10), POLICY["rounding"])
        if mode == "max":
            return max(1000, _round(Fraction(subtotal, 10), POLICY["rounding"]))
        raise AssertionError(mode)
    if member:
        return _round(Fraction(subtotal, 10), POLICY["rounding"])
    if coupon_ok:
        return 1000
    return 0


def _weekend(placed_at):
    local_we = placed_at.weekday() >= 5
    utc_we = placed_at.astimezone(datetime.timezone.utc).weekday() >= 5
    if local_we == utc_we:
        return local_we
    mode = POLICY["weekend"]
    if mode == "raise":
        raise NotSpecified("Which clock decides Saturday/Sunday for R-08?")
    return local_we if mode == "local" else utc_we


def _shipping(subtotal, placed_at):
    if _weekend(placed_at):
        return 0
    if subtotal > 5000:
        return 0
    if subtotal < 5000:
        return 499
    mode = POLICY["boundary"]
    if mode == "raise":
        raise NotSpecified("What is shipping at a subtotal of exactly 5000?")
    return 0 if mode == "free" else 499


def price_order(lines, placed_at, member=False, coupon=None):
    _refuse_all()
    _validate_lines(lines)
    if not isinstance(placed_at, datetime.datetime) or placed_at.utcoffset() is None:
        raise InvalidOrder("placed_at")
    if not isinstance(member, bool):
        raise InvalidOrder("member")
    if coupon is not None and coupon != "TEN":
        raise InvalidOrder("coupon")
    subtotal = sum(l["unit_cents"] * l["qty"] for l in lines if l["status"] == "active")
    coupon_ok = coupon == "TEN" and subtotal >= 5000
    discount = _discount(subtotal, member, coupon_ok)
    shipping = _shipping(subtotal, placed_at)
    return {"subtotal": subtotal, "discount": discount, "shipping": shipping,
            "total": subtotal - discount + shipping}


def loyalty_points(lines):
    _refuse_all()
    _validate_lines(lines)
    has_cancelled = any(l["status"] == "cancelled" for l in lines)
    mode = POLICY["cancelled_points"]
    if has_cancelled and mode == "raise":
        raise NotSpecified("Do cancelled lines earn loyalty points?")
    counted = [l for l in lines if mode == "all" or l["status"] == "active"]
    items = sum(l["qty"] for l in counted)
    return items + (50 if items >= 10 else 0)
