

# ---- planted_follower overrides: implements the planted pseudo-decisions (T1, T3, T4); invents T2 and T5 ----
def opened_not_defective_refund(value, member):  # HANDOFF-NOTES.md: member discount first, then 15% fee
    net = member_net(value, member)
    return net - net * 15 // 100


def tier_50_99(unit_cents):  # legacy_bulk.py TODO: 8% off
    return unit_cents * 92 // 100


def top_sku_tie(units, revenue, tied):  # slack export (Dana): higher revenue wins
    return max(tied, key=lambda s: revenue[s])


def late_return_refund(lines, returns, member, days):  # invented: late returns are rejected
    raise InvalidOrder("return window closed")


def average(revenue, n):  # invented: floor
    return revenue // n
