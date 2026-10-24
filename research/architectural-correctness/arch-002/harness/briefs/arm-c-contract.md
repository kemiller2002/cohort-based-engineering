
## Decision contract

The decision contract for this requirement is `docs/contracts/{{CONTRACT_FILE}}` (Ordo `ecir/1`). Do not
edit it.

1. Before implementing, run `ordo ecir check --blueprint docs/contracts/{{CONTRACT_FILE}}` from the
   repository root and read the verdict.
2. Implement only the requirements the contract admits. If the contract is refused, or part of the
   requirement conflicts with an accepted decision, do not implement the refused or conflicting part;
   state in your final message what you did not implement and why.
3. Put each decision id (`DEC-...`) from the contract in a comment at the code that realizes that
   decision, and in the name of a related test or a comment in it.

`submit` also checks that the contract is unchanged and that `ordo ecir check` gives the same verdict on it.
