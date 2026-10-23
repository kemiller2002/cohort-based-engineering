# DEC-B04: Sales tax

Status: accepted (2026-02-10, owner: Finance). Not yet implemented.

Each invoice adds sales tax on its amount at the rate of the customer's region, as listed in `docs/tax-rates.md`
(rounded to the cent, half away from zero). The late fee is charged on the amount before tax.
