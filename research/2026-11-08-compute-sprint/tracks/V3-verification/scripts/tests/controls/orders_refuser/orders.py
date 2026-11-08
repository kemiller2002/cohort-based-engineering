class InvalidInput(Exception): pass
class CouponNotApplicable(Exception): pass
class UnspecifiedPolicy(Exception): pass
def line_total(p, q): raise UnspecifiedPolicy("everything")
def order_total(lines, coupon=None): raise UnspecifiedPolicy("everything")
