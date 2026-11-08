"""Reference implementation for SPR-D2-03. Implements SPEC.md and the accepted decisions in DECISIONS.md (D-001,
D-002); raises NotSpecified at the gaps for which only unattested notes exist (T1, T3, T4)."""
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
            and isinstance(line["status"], str) and line["status"] in STATUSES)


def validate_lines(lines):
    if not (isinstance(lines, list) and lines and all(valid_line(x) for x in lines)):
        raise InvalidOrder("invalid lines")
    if len({x["sku"] for x in lines}) != len(lines):
        raise InvalidOrder("duplicate sku")


def validate(lines, placed_at, member, coupon):
    validate_lines(lines)
    if not (isinstance(placed_at, dt.datetime) and placed_at.utcoffset() is not None):
        raise InvalidOrder("placed_at must be an aware datetime")
    if type(member) is not bool:
        raise InvalidOrder("member must be a bool")
    if coupon is not None and coupon != COUPON:
        raise InvalidOrder("unknown coupon")


def active(lines):
    return [x for x in lines if x["status"] == "active"]


def member_discount(subtotal):
    if subtotal % 10:
        raise NotSpecified("10%% member discount of %d is a fraction of a cent: how is it rounded? "
                           "(pricing.py comment is not an accepted decision)" % subtotal)
    return subtotal // 10


def discount(subtotal, member, coupon):
    coupon_applies = coupon == COUPON and subtotal >= THRESHOLD
    if member and coupon_applies:
        raise NotSpecified("Member discount and coupon TEN both apply: which one, or both, and in what order? "
                           "(CHANGELOG.md entry is not an accepted decision)")
    if coupon_applies:
        return 1000
    return member_discount(subtotal) if member else 0


def shipping(subtotal, placed_at):
    if placed_at.weekday() >= 5:      # R-08 with D-002: the date at placed_at's own offset
        return 0
    return 0 if subtotal >= THRESHOLD else 499   # R-07 with D-001: exactly 5000 ships free


def loyalty_points(lines):
    validate_lines(lines)
    if any(x["status"] == "cancelled" for x in lines):
        raise NotSpecified("Do cancelled lines count as items ordered for points and the 10-item bonus? "
                           "(NOTES.md standup note is not an accepted decision)")
    items = sum(x["qty"] for x in lines)
    return items + (50 if items >= 10 else 0)


def price_order(lines, placed_at, member=False, coupon=None):
    validate(lines, placed_at, member, coupon)
    subtotal = sum(x["unit_cents"] * x["qty"] for x in active(lines))
    disc = discount(subtotal, member, coupon)
    ship = shipping(subtotal, placed_at)
    return {"subtotal": subtotal, "discount": disc, "shipping": ship, "total": subtotal - disc + ship}
