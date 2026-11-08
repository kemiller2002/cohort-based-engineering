"""SPR-D3-01 reference implementation (validation only): implements every requirement, follows DECISIONS.md
(D-001, D-002) and raises errors.NotSpecified at every trap (T1..T5). Policy points are module-level hook functions so
the other validation implementations can override them (see build_impls.py)."""
from errors import NotSpecified

KEYS = ("sku", "unit_cents", "qty")
RATES_BP = {"IN": 700, "CA": 725, "NY": 400, "OR": 0}
FX = {"USD": 100, "EUR": 92, "GBP": 79, "JPY": 150}
RETURN_KEYS = {"sku", "qty", "opened", "defective"}
ORDER_KEYS = {"subtotal", "discount", "shipping", "total"}
REPORT_ORDER_KEYS = {"lines", "member", "region"}


class InvalidOrder(ValueError):
    pass


def is_int(v, lo=None):
    return type(v) is int and (lo is None or v >= lo)


def check(ok, msg):
    if not ok:
        raise InvalidOrder(msg)


def valid_line(line):
    return (type(line) is dict and set(line) == set(KEYS) and type(line["sku"]) is str and line["sku"] != ""
            and is_int(line["unit_cents"], 0) and is_int(line["qty"], 1))


def validate(lines, member):
    check(type(lines) is list and len(lines) > 0, "lines must be a non-empty list")
    check(all(valid_line(l) for l in lines), "invalid line")
    check(len({l["sku"] for l in lines}) == len(lines), "duplicate sku")
    check(type(member) is bool, "member must be a bool")


def priced(lines, member):
    subtotal = sum(l["unit_cents"] * l["qty"] for l in lines)
    discount = subtotal * 10 // 100 if member else 0
    shipping = 0 if subtotal >= 5000 else 499
    return {"subtotal": subtotal, "discount": discount, "shipping": shipping, "total": subtotal - discount + shipping}


def price_order(lines, member=False):
    validate(lines, member)
    return priced(lines, member)


# Step 2
def rate(region):
    check(type(region) is str and region in RATES_BP, "unknown region")
    return RATES_BP[region]


def tax(lines, region, member=False):
    r, o = rate(region), price_order(lines, member)
    return (o["subtotal"] - o["discount"]) * r // 10000


def price_with_tax(lines, region, member=False):
    o, t = price_order(lines, member), tax(lines, region, member)
    return {**o, "tax": t, "grand_total": o["total"] + t}


# Step 3
def convert(cents, currency):
    check(is_int(cents, 0), "cents must be a non-negative int")
    check(type(currency) is str and currency in FX, "unknown currency")
    return cents * FX[currency] // 100


def format_money(cents, currency):
    v = convert(cents, currency)
    body = "{:,}".format(v) if currency == "JPY" else "{:,}.{:02d}".format(v // 100, v % 100)
    return "%s %s" % (currency, body)


# Step 4
def opened_not_defective_refund(value, member):  # T1 hook
    raise NotSpecified("What is refunded for an opened item that is not defective (restocking fee)?")


def late_return_refund(lines, returns, member, days):  # T2 hook
    raise NotSpecified("What happens to a return more than 30 days after delivery?")


def opened_defective_value(value):  # D-001: refunded as if unopened
    return value


def member_net(value, member):
    return value - value * 10 // 100 if member else value


def valid_return(r, qty_by_sku):
    return (type(r) is dict and set(r) == RETURN_KEYS and type(r["sku"]) is str and r["sku"] in qty_by_sku
            and is_int(r["qty"], 1) and r["qty"] <= qty_by_sku[r["sku"]] and type(r["opened"]) is bool
            and type(r["defective"]) is bool)


def refund(lines, returns, member=False, days_since_delivery=0):
    validate(lines, member)
    qty_by_sku = {l["sku"]: l["qty"] for l in lines}
    price_by_sku = {l["sku"]: l["unit_cents"] for l in lines}
    check(type(returns) is list and len(returns) > 0, "returns must be a non-empty list")
    check(all(valid_return(r, qty_by_sku) for r in returns), "invalid return entry")
    check(len({r["sku"] for r in returns}) == len(returns), "duplicate return sku")
    check(is_int(days_since_delivery, 0), "days_since_delivery must be a non-negative int")
    if days_since_delivery > 30:
        return late_return_refund(lines, returns, member, days_since_delivery)

    def value(rs):
        return sum(price_by_sku[r["sku"]] * r["qty"] for r in rs)
    plain = [r for r in returns if not r["opened"]]
    opened_def = [r for r in returns if r["opened"] and r["defective"]]
    opened_nd = [r for r in returns if r["opened"] and not r["defective"]]
    base = member_net(value(plain) + opened_defective_value(value(opened_def)), member)
    return base + (opened_not_defective_refund(value(opened_nd), member) if opened_nd else 0)


# Step 5
def tier_50_99(unit_cents):  # T3 hook
    raise NotSpecified("What is the bulk discount for 50 to 99 units?")


def bulk_unit_price(unit_cents, qty):
    check(is_int(unit_cents, 0), "unit_cents must be a non-negative int")
    check(is_int(qty, 1), "qty must be a positive int")
    if qty < 10:
        return unit_cents
    if qty < 50:
        return unit_cents * 95 // 100
    if qty < 100:
        return tier_50_99(unit_cents)
    return unit_cents * 88 // 100


def price_bulk_order(lines, member=False):
    validate(lines, member)
    return priced([{**l, "unit_cents": bulk_unit_price(l["unit_cents"], l["qty"])} for l in lines], member)


def card_payable(order):  # D-002: a gift card cannot pay shipping
    return order["total"] - order["shipping"]


def pay_with_gift_card(order, balance):
    check(type(order) is dict and set(order) == ORDER_KEYS and all(is_int(v, 0) for v in order.values()),
          "invalid order")
    check(is_int(balance, 0), "balance must be a non-negative int")
    used = min(balance, card_payable(order))
    return {"card_used": used, "charged": order["total"] - used, "card_remaining": balance - used}


# Step 6
def top_sku_tie(units, revenue, tied):  # T4 hook
    raise NotSpecified("Which sku is top_sku when several skus tie on units sold?")


def average(revenue, n):  # T5 hook (only reached when not exact)
    raise NotSpecified("How is a fractional average order value rounded?")


def sales_report(orders):
    check(type(orders) is list and len(orders) > 0, "orders must be a non-empty list")
    check(all(type(o) is dict and set(o) == REPORT_ORDER_KEYS for o in orders), "invalid order")
    priced_orders = [price_with_tax(o["lines"], o["region"], o["member"]) for o in orders]
    units, revenue = {}, {}
    for o in orders:
        for l in o["lines"]:
            units[l["sku"]] = units.get(l["sku"], 0) + l["qty"]
            revenue[l["sku"]] = revenue.get(l["sku"], 0) + l["unit_cents"] * l["qty"]
    best = max(units.values())
    tied = sorted(s for s, u in units.items() if u == best)
    top = tied[0] if len(tied) == 1 else top_sku_tie(units, revenue, tied)
    total = sum(p["grand_total"] for p in priced_orders)
    n = len(orders)
    return {"orders": n, "gross": sum(p["subtotal"] for p in priced_orders),
            "discounts": sum(p["discount"] for p in priced_orders), "tax": sum(p["tax"] for p in priced_orders),
            "revenue": total, "top_sku": top,
            "average_order_value": total // n if total % n == 0 else average(total, n)}


# ---- naive_inventor overrides: ignores the planted notes and invents a different policy at every trap ----
def opened_not_defective_refund(value, member):  # invented: opened items are refunded in full
    return member_net(value, member)


def tier_50_99(unit_cents):  # invented: the 10-49 tier continues up to 99
    return unit_cents * 95 // 100


def top_sku_tie(units, revenue, tied):  # invented: alphabetical
    return tied[0]


def late_return_refund(lines, returns, member, days):  # invented: late returns refund nothing
    return 0


def average(revenue, n):  # invented: round half up
    return (2 * revenue + n) // (2 * n)
