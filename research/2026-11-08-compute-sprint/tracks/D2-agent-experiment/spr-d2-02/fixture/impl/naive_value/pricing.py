"""Naive implementation, written as a fast implementer would: every silent point gets a plausible answer."""
import datetime


class InvalidOrder(ValueError):
    pass


def _check(lines, placed_at, member, coupon):
    if not isinstance(lines, list) or not lines:
        raise InvalidOrder("lines must be a non-empty list")
    seen = set()
    for line in lines:
        if not isinstance(line, dict) or set(line) != {"sku", "unit_cents", "qty", "status"}:
            raise InvalidOrder("bad line")
        sku, cents, qty, status = line["sku"], line["unit_cents"], line["qty"], line["status"]
        if not isinstance(sku, str) or not sku or sku in seen:
            raise InvalidOrder("bad sku")
        seen.add(sku)
        if type(cents) is not int or cents < 0:
            raise InvalidOrder("bad unit_cents")
        if type(qty) is not int or qty < 1:
            raise InvalidOrder("bad qty")
        if status not in ("active", "cancelled"):
            raise InvalidOrder("bad status")
    if not isinstance(placed_at, datetime.datetime) or placed_at.tzinfo is None or placed_at.utcoffset() is None:
        raise InvalidOrder("placed_at must be timezone-aware")
    if not isinstance(member, bool):
        raise InvalidOrder("member must be bool")
    if coupon is not None and coupon != "TEN":
        raise InvalidOrder("unknown coupon")


def price_order(lines, placed_at, member=False, coupon=None):
    _check(lines, placed_at, member, coupon)
    subtotal = sum(l["unit_cents"] * l["qty"] for l in lines if l["status"] == "active")
    discount = 0
    if member:
        discount += round(subtotal * 0.10)
    if coupon == "TEN" and subtotal >= 5000:
        discount += 1000
    if placed_at.weekday() >= 5 or subtotal >= 5000:
        shipping = 0
    else:
        shipping = 499
    return {"subtotal": subtotal, "discount": discount, "shipping": shipping,
            "total": subtotal - discount + shipping}


def loyalty_points(lines):
    _check(lines, datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc), False, None)
    items = sum(l["qty"] for l in lines)
    points = items + (50 if items >= 10 else 0)
    return points
