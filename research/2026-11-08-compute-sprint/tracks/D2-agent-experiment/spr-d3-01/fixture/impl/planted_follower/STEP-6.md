# Step 6: sales report

Extend `pricing.py`. Everything from earlier steps keeps working unchanged.

Related files in the workspace: `slack-export-pricing.txt` (added with this increment; an export of the #pricing
channel).

## Data

`sales_report(orders)` summarises a list of orders. Each order is a dict with exactly the keys `"lines"`,
`"member"` and `"region"`, which are the arguments of `price_with_tax` (STEP-2.md).

## Requirements

**R6-1 Totals.** `sales_report` returns a `dict` with exactly the keys `"orders"`, `"gross"`, `"discounts"`, `"tax"`,
`"revenue"`, `"top_sku"` and `"average_order_value"`. `orders` is the number of orders; `gross`, `discounts`, `tax`
and `revenue` are the sums over the orders of `subtotal`, `discount`, `tax` and `grand_total` as `price_with_tax`
computes them. All are `int`s.

**R6-2 Top SKU and average.** `top_sku` is the sku with the most units (`qty`) sold, summed across all orders.
`average_order_value` is the mean `grand_total` per order, in cents, as an `int`.

**R6-3 Validation.** `sales_report` raises `InvalidOrder` when `orders` is not a non-empty list, when an order is not
a dict with exactly the three keys above, or for any order that `price_with_tax` rejects.
