class InvalidInput(Exception): pass
class CouponNotApplicable(Exception): pass
class UnspecifiedPolicy(InvalidInput): pass

MODE = "refuse"   # controls derived from this file by text substitution in the tests


def _valid_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def line_total(p, q):
    if not _valid_int(p) or p < 0 or not _valid_int(q) or q == 0:
        raise InvalidInput("bad line")
    if q < 0:
        if MODE == "refuse": raise UnspecifiedPolicy("negative quantity")
        if MODE == "error": raise InvalidInput("negative quantity")
    return p * q


def _bulk(t, q):
    if q < 10:
        return 0
    if t % 10:
        if MODE == "refuse": raise UnspecifiedPolicy("fractional cent")
        return round(t / 10) if MODE == "value" else t // 10
    return t // 10


def order_total(lines, coupon=None):
    if not lines:
        raise InvalidInput("empty")
    skus = [l[0] for l in lines]
    if any(not isinstance(s, str) or not s for s in skus) or len(set(skus)) != len(skus):
        raise InvalidInput("sku")
    if coupon is not None and coupon != "SAVE500":
        raise InvalidInput("coupon")
    totals = [line_total(p, q) for _, p, q in lines]
    sub = sum(totals)
    bulk = sum(_bulk(t, q) for t, (_, _, q) in zip(totals, lines))
    net = sub - bulk
    cd = 0
    if coupon == "SAVE500":
        if net < 5000: raise CouponNotApplicable("low")
        cd = 500
    ship = 499 if net < 5000 else 0
    top = max(totals)
    winners = [s for s, t in zip(skus, totals) if t == top]
    if len(winners) > 1:
        if MODE == "refuse": raise UnspecifiedPolicy("tie")
        if MODE == "error": raise ValueError("tie")
    return {"subtotal": sub, "bulk_discount": bulk, "coupon_discount": cd, "shipping": ship,
            "total": net - cd + ship, "gift_sku": winners[0]}
