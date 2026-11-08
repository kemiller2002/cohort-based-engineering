# Handoff notes (Marco Bell, previous developer)

I'm moving to the checkout team on Monday; here is where returns stood when I left.

- Return requests come from the support tool as a list of `{sku, qty, opened, defective}` entries, one per sku.
- Refunds are computed per order, never across orders.
- Restocking fee: opened items that are not defective pay a 15% restocking fee. The fee is 15% of the opened units'
  price, rounded down to the cent, and is deducted from their refund (member discount first, then the fee on what is
  left). Dana and I settled this in the hallway after the returns review, so it's final; just wire it in.
- Shipping is never refunded and never clawed back.
- Support tool sends `days_since_delivery` as an int, already computed in the warehouse's time zone.
