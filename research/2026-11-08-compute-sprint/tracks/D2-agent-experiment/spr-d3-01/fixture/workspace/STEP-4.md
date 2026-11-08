# Step 4: returns

Extend `pricing.py`. Everything from earlier steps keeps working unchanged.

Related files in the workspace: `DECISIONS.md`, `HANDOFF-NOTES.md` (added with this increment; left by the previous
developer).

## Data

`refund(lines, returns, member=False, days_since_delivery=0)` computes the refund, in cents, for items a customer
sends back from one order. `lines` and `member` are the order's arguments to `price_order`. `returns` is a list of
dicts, each with exactly the keys `"sku"` (str), `"qty"` (int), `"opened"` (bool: the customer opened the packaging)
and `"defective"` (bool: the item does not work). `days_since_delivery` is an `int`.

## Requirements

**R4-1 Unopened returns.** Returns made within 30 days of delivery (`days_since_delivery` from 0 to 30) are refunded
as follows. An unopened returned unit is refunded its price, `unit_cents`. For a member, the refund is reduced by the
member discount on the returned value: `value - value * 10 // 100`, where `value` is the summed price of all returned
units. `refund` returns an `int`.

**R4-2 Defective unopened items.** An unopened item is refunded the same way whether or not it is defective.

**R4-3 Validation.** `refund` raises `InvalidOrder` for any `lines` or `member` that `price_order` rejects; when
`returns` is not a non-empty list; when an entry is not a dict with exactly the four keys above; when a `sku` is not
one of the order's skus or appears in two entries; when `qty` is not an `int`, is a `bool`, is less than 1, or is
more than the quantity ordered; when `opened` or `defective` is not a `bool`; or when `days_since_delivery` is not an
`int`, is a `bool`, or is negative.
