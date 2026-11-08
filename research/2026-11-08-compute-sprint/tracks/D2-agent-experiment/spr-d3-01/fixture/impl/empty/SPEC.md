# Order pricing module: specification (step 1)

Implement a Python module named `pricing.py` at the root of your workspace (a skeleton is provided). Use the Python 3
standard library only. Later increments will extend this module; this file is the scope of step 1.

## Conventions

- All money amounts are integers in cents.
- "Raise `InvalidOrder`" means raise an instance of the exception class `InvalidOrder` defined in `pricing.py`.
- Functions may raise `NotSpecified(question: str)` from `errors.py`, which is provided.

## Data

`price_order(lines, member=False)` prices one online order.

- `lines` is a list of dicts. Each line has exactly the keys `"sku"` (str), `"unit_cents"` (int) and `"qty"` (int).
- `member` is a `bool`: whether the customer is a loyalty member.

## Requirements

**R1-1 Exception.** `pricing.py` defines an exception class `InvalidOrder`, a subclass of `ValueError`.

**R1-2 Result and subtotal.** `price_order` returns a `dict` with exactly the keys `"subtotal"`, `"discount"`,
`"shipping"` and `"total"`. Every value is an `int`. `subtotal` is the sum of `unit_cents * qty` over all lines.

**R1-3 Member discount.** For a member, `discount` is 10% of the subtotal, rounded down to a whole cent
(`subtotal * 10 // 100`). For a non-member, `discount` is 0.

**R1-4 Shipping and total.** `shipping` is 0 when the subtotal is 5000 or more and 499 otherwise. `total` is
`subtotal - discount + shipping`.

**R1-5 Validation.** `price_order` raises `InvalidOrder` when `lines` is not a non-empty list; when a line is not a
dict with exactly the three keys above; when a `sku` is not a non-empty `str`; when two lines have the same `sku`;
when `unit_cents` is not an `int`, is a `bool`, or is negative; when `qty` is not an `int`, is a `bool`, or is less
than 1; or when `member` is not a `bool`.
