"""Prototype bulk-discount table (Marco Bell). Not imported by anything; kept for reference."""

# Discount in basis points by minimum quantity.
# TODO(marco): 50-99 units get 8% off (800 bp). Confirmed with Dana on the 11/02 call; add it when bulk ships.
BULK_DISCOUNT_BP = {10: 500, 100: 1200}


def bulk_price_draft(unit_cents, qty):
    bp = max((d for q, d in BULK_DISCOUNT_BP.items() if qty >= q), default=0)
    return unit_cents * (10000 - bp) // 10000
