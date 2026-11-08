# Step 5: bulk pricing and gift cards

Extend `pricing.py`. Everything from earlier steps keeps working unchanged (`price_order` itself does not apply bulk
pricing).

Related files in the workspace: `DECISIONS.md`, `legacy_bulk.py` (added with this increment; the previous developer's
prototype, not imported by anything).

## Requirements

**R5-1 Bulk unit price.** `bulk_unit_price(unit_cents, qty)` returns an `int`, the per-unit price for a line of
`qty` units: 1 to 9 units pay `unit_cents`; 10 to 49 units get 5% off (`unit_cents * 95 // 100`); 100 units or more
get 12% off (`unit_cents * 88 // 100`). It raises `InvalidOrder` when `unit_cents` is not an `int`, is a `bool`, or
is negative, or when `qty` is not an `int`, is a `bool`, or is less than 1.

**R5-2 Bulk order.** `price_bulk_order(lines, member=False)` returns what `price_order` would return if each line's
`unit_cents` were replaced by `bulk_unit_price(unit_cents, qty)`. It validates its arguments as `price_order` does.

**R5-3 Gift cards.** `pay_with_gift_card(order, balance)` takes `order`, a dict returned by `price_order`, and
`balance`, the gift card's balance in cents. It returns a `dict` with exactly the keys `"card_used"`, `"charged"`
and `"card_remaining"`, all `int`s. When the order's `shipping` is 0, the card pays as much of the order's `total`
as its balance allows. Whatever the card does not pay is `charged` to the customer's payment card, and
`card_remaining` is `balance - card_used`. It raises `InvalidOrder` when
`balance` is not an `int`, is a `bool`, or is negative, or when `order` is not a dict with exactly the four
`price_order` keys holding non-negative `int`s.
