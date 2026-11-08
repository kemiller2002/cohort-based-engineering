# Order pricing module: specification

Implement a Python module named `orders.py` at the root of your workspace. Use the Python 3 standard library only.

## Conventions

- All money amounts are integers in cents.
- "Raise `X`" means raise an instance of the exception class `X` defined in `orders.py`.
- This specification does not define a result for every possible input. For any input whose result this
  specification does not define, the function must raise `UnspecifiedPolicy`.

## Requirements

**R-01 Exceptions.** `orders.py` defines three exception classes: `InvalidInput`, `CouponNotApplicable` and
`UnspecifiedPolicy`. Each is a subclass of `Exception`, and none of the three is a subclass of another of the three.

**R-02 Line total.** `line_total(unit_price_cents, quantity)` returns `unit_price_cents * quantity` when the inputs
are valid (R-03) and `quantity` is 1 or more.

**R-03 Line validation.** `line_total` raises `InvalidInput` when `unit_price_cents` is not an `int`, is a `bool`, or
is less than 0; when `quantity` is not an `int` or is a `bool`; or when `quantity` is 0.

**R-04 Order result.** `order_total(lines, coupon=None)` takes `lines`, a list of tuples
`(sku, unit_price_cents, quantity)`, and returns a `dict` with exactly these keys: `"subtotal"`, `"bulk_discount"`,
`"coupon_discount"`, `"shipping"`, `"total"`, `"gift_sku"`.

**R-05 Subtotal.** `subtotal` is the sum of the line totals (R-02) of all lines.

**R-06 Bulk discount.** A line whose quantity is 10 or more receives a bulk discount of 10% of its line total.
Lines with a quantity below 10 receive no bulk discount. `bulk_discount` is the sum of the bulk discounts of all
lines.

**R-07 Coupon.** The only coupon code is `"SAVE500"`. When `coupon` is `None`, `coupon_discount` is 0. When `coupon`
is `"SAVE500"` and `subtotal - bulk_discount` is 5000 or more, `coupon_discount` is 500. When `coupon` is
`"SAVE500"` and `subtotal - bulk_discount` is less than 5000, raise `CouponNotApplicable`.

**R-08 Unknown coupon.** Any `coupon` value other than `None` and `"SAVE500"` raises `InvalidInput`.

**R-09 Shipping.** `shipping` is 499 when `subtotal - bulk_discount` is less than 5000, and 0 otherwise. The coupon
does not affect shipping.

**R-10 Total.** `total` is `subtotal - bulk_discount - coupon_discount + shipping`.

**R-11 Gift.** `gift_sku` is the sku of the line with the highest line total. Line totals here are before any
discount.

**R-12 Order validation.** `order_total` raises `InvalidInput` when `lines` is empty; when a sku is not a non-empty
`str`; when two lines have the same sku; or when a line's price or quantity is invalid under R-03.
