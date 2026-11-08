# Accepted decisions

Decisions recorded here are part of the specification (see SPEC.md, Conventions).

## D-001 Shipping at a subtotal of exactly 5000

Decision: An order whose subtotal is exactly 5000 cents ships free (`shipping` is 0), on any day.

Signed-off-by: Dana Ruiz (product owner), 2026-11-03

## D-002 Which day decides weekend shipping

Decision: R-08 uses the calendar date of `placed_at` in its own UTC offset (the customer's device clock). An order
whose `placed_at` falls on a Saturday or a Sunday at that offset ships free, whatever the UTC date is.

Signed-off-by: Dana Ruiz (product owner), 2026-11-04
