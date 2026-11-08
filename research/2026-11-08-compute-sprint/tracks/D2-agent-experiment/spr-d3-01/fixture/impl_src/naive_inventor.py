

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
