# Step 2: sales tax

Extend `pricing.py`. Everything from SPEC.md keeps working unchanged.

## Requirements

**R2-1 Tax.** `tax(lines, region, member=False)` returns an `int`: the sales tax on the order, computed on
`subtotal - discount` (as defined in SPEC.md; shipping is not taxed) at the region's rate, rounded down to a whole
cent. Rates in basis points (1/100 of a percent): `"IN"` 700, `"CA"` 725, `"NY"` 400, `"OR"` 0. So the tax is
`(subtotal - discount) * rate // 10000`.

**R2-2 Priced with tax.** `price_with_tax(lines, region, member=False)` returns a `dict` with the four keys of
`price_order` (same values) plus `"tax"` (as R2-1) and `"grand_total"` (`total + tax`). Every value is an `int`.

**R2-3 Validation.** `tax` and `price_with_tax` raise `InvalidOrder` when `region` is not exactly one of the four
codes above (codes are case-sensitive), and for any `lines` or `member` that `price_order` rejects.
