# PRC-08: Invoice matching and payment scheduling

Requirements: PRC-08-R1, PRC-08-R2, PRC-08-R3. Owner: Accounts Payable.

## PRC-08-R1

Every purchase needs a purchase order before it is paid, whatever its amount.

## PRC-08-R2

An invoice is approved for payment when every line matches its purchase order line: same item, same quantity, and a
unit price within the price tolerance in force.

## PRC-08-R3

An approved invoice is scheduled for payment on the date its vendor's payment terms give, under the terms decision in
force.

Acceptance criteria: each statement above holds; existing behaviour is unchanged except as these requirements say.
