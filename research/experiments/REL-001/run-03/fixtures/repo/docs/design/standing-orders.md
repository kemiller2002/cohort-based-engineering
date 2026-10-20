# Design note: standing orders

Status: accepted. Owner: Payments.

## Purpose

Customers set up recurring payments from one account to another on a fixed
day of the month. A nightly job runs every day with the full list of the
ledger's standing orders and the new business date; the ledger decides which
orders are due and pays them.

## When the source cannot cover the payment

**Rule: a standing order is paid in full or not at all.** If the source
account cannot cover the whole amount, nothing is moved for that order on
that run and the order is reported as skipped with the refusal the transfer
gave. The ledger never pays part of an order, and it never borrows from a
later order's funds.

A skipped order is not carried over to the next day's run. If the customer
adds funds the same business day and the job runs again for that date, the
order is paid then.

## Rejected alternative

Paying whatever the source holds and recording the shortfall was considered
and rejected: it creates partial payments that customers and payees cannot
reconcile against the agreed amount.
