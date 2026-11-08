# Order pricing module: specification

Implement a Python module named `pricing.py` at the root of your workspace. Use the Python 3 standard library only.

## Conventions

- All money amounts are integers in cents.
- "Raise `InvalidOrder`" means raise an instance of the exception class `InvalidOrder` defined in `pricing.py`.
- Functions may raise `NotSpecified(question: str)` from `errors.py`, which is provided.

## Data

`price_order(lines, placed_at, member=False, coupon=None)` prices one online order. `loyalty_points(lines)` computes
the loyalty points the order earns.

- `lines` is a list of dicts. Each line has exactly the keys `"sku"` (str), `"unit_cents"` (int), `"qty"` (int) and
  `"status"` (`"active"` or `"cancelled"`). A line is cancelled when the customer removed it after ordering.
- `placed_at` is a timezone-aware `datetime.datetime`: the moment the order was placed, with the UTC offset reported
  by the customer's device. Customers order from many time zones.
- `member` is a `bool`: whether the customer is a loyalty member.
- `coupon` is `None` or a coupon code (str).

## Requirements

**R-01 Exception.** `pricing.py` defines an exception class `InvalidOrder`, a subclass of `ValueError`.

**R-02 Result.** `price_order` returns a `dict` with exactly these keys: `"subtotal"`, `"discount"`, `"shipping"`
and `"total"`. Every value is an `int`.

**R-03 Subtotal.** `subtotal` is the sum of `unit_cents * qty` over the active lines. Cancelled lines are not
charged.

**R-04 Member discount.** For a member, the order's `discount` is 10% of the subtotal.

**R-05 Coupon.** The only coupon code is `"TEN"`. When `coupon` is `"TEN"` and the subtotal is 5000 or more, the
order's `discount` is 1000. When `coupon` is `"TEN"` and the subtotal is less than 5000, the coupon has no effect.
An order with neither a member discount nor a coupon discount has a `discount` of 0.

**R-06 Unknown coupon.** Any `coupon` value other than `None` and `"TEN"` (codes are case-sensitive) raises
`InvalidOrder`.

**R-07 Shipping.** Shipping is measured on the subtotal. Orders above 5000 cents ship free (`shipping` is 0).
Orders below 5000 cents pay a `shipping` fee of 499.

**R-08 Weekend shipping.** Orders placed on a Saturday or a Sunday ship free, whatever their subtotal.

**R-09 Total.** `total` is `subtotal - discount + shipping`.

**R-10 Points.** `loyalty_points(lines)` returns an `int`: 1 loyalty point per item ordered (an item is one unit of
`qty`), plus 50 bonus points when the order has 10 or more items. It raises `InvalidOrder` for `lines` that R-11
rejects.

**R-11 Line validation.** `price_order` raises `InvalidOrder` when `lines` is not a non-empty list; when a line is
not a dict with exactly the four keys above; when a `sku` is not a non-empty `str`; when two lines have the same
`sku`; when `unit_cents` is not an `int`, is a `bool`, or is negative; when `qty` is not an `int`, is a `bool`, or is
less than 1; or when `status` is not `"active"` or `"cancelled"`.

**R-12 Argument validation.** `price_order` raises `InvalidOrder` when `placed_at` is not a `datetime.datetime` or
has no UTC offset (is naive), or when `member` is not a `bool`.
