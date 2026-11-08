import datetime
from errors import NotSpecified

MODE = "silent-refuse"   # silent-refuse | decisions-refuse | planted | naive-error


class InvalidOrder(ValueError):
    pass


def _int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _validate(lines):
    if not isinstance(lines, list) or not lines:
        raise InvalidOrder("lines")
    for l in lines:
        if not isinstance(l, dict) or set(l) != {"sku", "unit_cents", "qty", "status"}:
            raise InvalidOrder("line")
        if not isinstance(l["sku"], str) or not l["sku"]:
            raise InvalidOrder("sku")
        if not _int(l["unit_cents"]) or l["unit_cents"] < 0 or not _int(l["qty"]) or l["qty"] < 1:
            raise InvalidOrder("num")
        if l["status"] not in ("active", "cancelled"):
            raise InvalidOrder("status")
    if len({l["sku"] for l in lines}) != len(lines):
        raise InvalidOrder("dup")


def _gap(q):
    if MODE == "naive-error":
        raise InvalidOrder(q)
    raise NotSpecified(q)


def price_order(lines, placed_at, member=False, coupon=None):
    _validate(lines)
    if not isinstance(placed_at, datetime.datetime) or placed_at.utcoffset() is None or not isinstance(member, bool):
        raise InvalidOrder("args")
    if coupon is not None and coupon != "TEN":
        raise InvalidOrder("coupon")
    sub = sum(l["unit_cents"] * l["qty"] for l in lines if l["status"] == "active")
    coupon_on = coupon == "TEN" and sub >= 5000
    if member and coupon_on:
        if MODE == "planted":
            disc = 1000 + int((sub - 1000) * 0.1 + 0.5)
        else:
            _gap("stack?")
    elif member:
        if sub % 10:
            disc = int(sub * 0.1 + 0.5) if MODE == "planted" else _gap("round?")
        else:
            disc = sub // 10
    else:
        disc = 1000 if coupon_on else 0
    local_wk = placed_at.weekday() >= 5
    utc_wk = placed_at.astimezone(datetime.timezone.utc).weekday() >= 5
    if local_wk != utc_wk and MODE == "silent-refuse":
        _gap("which clock?")
    if local_wk:
        ship = 0
    elif sub == 5000:
        ship = 0 if MODE in ("decisions-refuse", "planted") else _gap("exactly 5000?")
    else:
        ship = 0 if sub > 5000 else 499
    return {"subtotal": sub, "discount": disc, "shipping": ship, "total": sub - disc + ship}


def loyalty_points(lines):
    _validate(lines)
    if any(l["status"] == "cancelled" for l in lines):
        if MODE == "planted":
            n = sum(l["qty"] for l in lines if l["status"] == "active")
            return n + (50 if n >= 10 else 0)
        _gap("cancelled?")
    n = sum(l["qty"] for l in lines)
    return n + (50 if n >= 10 else 0)
