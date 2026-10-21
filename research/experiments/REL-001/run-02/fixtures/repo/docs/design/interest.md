# Design note: tiered interest

Status: accepted. Owner: Treasury.

## How tiers apply to a balance

A rate schedule is an ordered list of tiers. Each tier covers the slice of
a balance above the previous tier's `UpTo` (0 for the first tier) and up to
and including its own `UpTo`; the last tier has no upper limit.

**Rule: interest is marginal.** Each slice of the balance earns the rate of
the tier that covers that slice. A balance never earns a higher tier's rate
on the part of it that lies in a lower tier. The interest for a balance is
the sum of the interest on its slices.

Worked example. Schedule: up to 1,000 at 1%; up to 5,000 at 2%; above that
at 3%. A balance of 6,000 earns

    1,000 x 0.01 + 4,000 x 0.02 + 1,000 x 0.03 = 10 + 80 + 30 = 120

and not 6,000 x 0.03 = 180.

The sum is rounded once, at the end (see the requirement for the rounding
mode), never slice by slice.

## Rejected alternative

Applying the rate of the highest tier reached to the whole balance was
rejected: it makes interest jump at every tier boundary (a balance of
1,000.01 would earn more than twice as much as 1,000.00), which Treasury
does not accept.
