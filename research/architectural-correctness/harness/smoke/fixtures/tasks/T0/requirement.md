# T0 (smoke stand-in): late fee

LENDING-T0-R1. Add `Fees.lateFee (daysLate: int) : int` in `Lending.Semantic`: the fee in cents is
`daysLate * Fees.dailyLateFeeCents`, and 0 when `daysLate <= 0`.
