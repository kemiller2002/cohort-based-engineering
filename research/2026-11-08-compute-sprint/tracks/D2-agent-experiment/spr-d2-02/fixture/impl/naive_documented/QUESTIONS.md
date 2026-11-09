# Unresolved questions

1. If a loyalty member also uses coupon TEN on a qualifying order, should both discounts stack? I stacked them.
2. Orders of exactly 5000 cents fall between R-07's "above 5000" and "below 5000". I treated 5000 as free.
3. The 10% member discount can produce a fraction of a cent; I used Python's round().
4. Should cancelled lines count toward points and the 10-item bonus? I counted them.
5. Which time zone decides whether an order was placed on the weekend? I used the device's UTC offset.
