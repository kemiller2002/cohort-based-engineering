# Step 3: multi-currency display

Extend `pricing.py`. Everything from earlier steps keeps working unchanged.

## Requirements

**R3-1 Conversion.** `convert(cents, currency)` returns an `int`: the amount in the currency's smallest unit,
rounded down. Rates per 100 US cents: `"USD"` 100 (cents), `"EUR"` 92 (euro cents), `"GBP"` 79 (pence), `"JPY"` 150
(yen). So the result is `cents * rate // 100`.

**R3-2 Formatting.** `format_money(cents, currency)` returns a `str`: the currency code, one space, then the
converted amount (R3-1) with a comma between groups of three digits. USD, EUR and GBP show the amount in major units
with exactly two decimals (`"USD 1,234.56"`, `"EUR 0.92"`); JPY has no decimals (`"JPY 1,851"`).

**R3-3 Validation.** `convert` and `format_money` raise `InvalidOrder` when `cents` is not an `int`, is a `bool`, or
is negative, and when `currency` is not exactly one of the four codes above.
