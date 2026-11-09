# Decisions

## D-001 Opened items returned as defective

Decision: An opened item that is returned as defective (`"opened": true, "defective": true`) is refunded exactly as
if it were unopened: its price, less the member discount for members. Nothing is deducted for the opened packaging.

Signed-off-by: Dana Ruiz (product owner), 2026-11-03

## D-002 Gift cards and shipping

Decision: A gift card cannot pay for shipping. The card pays at most `total - shipping`; the order's shipping fee is
always charged to the customer's payment card.

Signed-off-by: Dana Ruiz (product owner), 2026-11-04
