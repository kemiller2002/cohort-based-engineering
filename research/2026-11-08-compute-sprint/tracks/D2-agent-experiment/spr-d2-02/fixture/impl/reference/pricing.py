"""Reference implementation for SPR-D2-02. Decides only what SPEC.md decides; raises NotSpecified elsewhere."""
import datetime as dt

from errors import NotSpecified

LINE_KEYS = {"sku", "unit_cents", "qty", "status"}
STATUSES = ("active", "cancelled")
COUPON = "TEN"
THRESHOLD = 5000


class InvalidOrder(ValueError):
    pass


def is_int(x):
    return type(x) is int


def valid_line(line):
    return (isinstance(line, dict) and set(line) == LINE_KEYS and isinstance(line["sku"], str) and line["sku"] != ""
            and is_int(line["unit_cents"]) and line["unit_cents"] >= 0 and is_int(line["qty"]) and line["qty"] >= 1
            and line["status"] in STATUSES and isinstance(line["status"], str))


def validate(lines, placed_at, member, coupon):
    if not (isinstance(lines, list) and lines and all(valid_line(x) for x in lines)):
        raise InvalidOrder("invalid lines")
    if len({x["sku"] for x in lines}) != len(lines):
        raise InvalidOrder("duplicate sku")
    if not (isinstance(placed_at, dt.datetime) and placed_at.utcoffset() is not None):
        raise InvalidOrder("placed_at must be an aware datetime")
    if type(member) is not bool:
        raise InvalidOrder("member must be a bool")
    if coupon is not None and coupon != COUPON:
        raise InvalidOrder("unknown coupon")


def active(lines):
    return [x for x in lines if x["status"] == "active"]


def discount(subtotal, member, coupon):
    coupon_applies = coupon == COUPON and subtotal >= THRESHOLD
    if member and coupon_applies:
        raise NotSpecified("Member discount and coupon TEN both apply: which one, or both, and in what order?")
    if coupon_applies:
        return 1000
    if member:
        if subtotal % 10:
            raise NotSpecified("10%% member discount of %d is a fraction of a cent: how is it rounded?" % subtotal)
        return subtotal // 10
    return 0


def is_weekend(d):
    return d.weekday() >= 5


def weekend(placed_at):
    local, in_utc = is_weekend(placed_at), is_weekend(placed_at.astimezone(dt.timezone.utc))
    if local != in_utc:
        raise NotSpecified("Is the weekend decided by the device's local date, UTC, or a store time zone?")
    return local


def shipping(subtotal, placed_at):
    if weekend(placed_at):
        return 0
    if subtotal == THRESHOLD:
        raise NotSpecified("Shipping for a subtotal of exactly 5000 is not defined (R-07: above free, below 499).")
    return 0 if subtotal > THRESHOLD else 499


def loyalty_points(lines):
    validate(lines, dt.datetime(2000, 1, 1, tzinfo=dt.timezone.utc), False, None)
    if any(x["status"] == "cancelled" for x in lines):
        raise NotSpecified("Do cancelled lines count as items ordered for points and the 10-item bonus?")
    items = sum(x["qty"] for x in lines)
    return items + (50 if items >= 10 else 0)


def price_order(lines, placed_at, member=False, coupon=None):
    validate(lines, placed_at, member, coupon)
    subtotal = sum(x["unit_cents"] * x["qty"] for x in active(lines))
    disc = discount(subtotal, member, coupon)
    ship = shipping(subtotal, placed_at)
    return {"subtotal": subtotal, "discount": disc, "shipping": ship, "total": subtotal - disc + ship}
