# Decisions

Accepted decisions for the booking module. Each entry has an ID and a Signed-off-by line.

## D-001: Who may cancel a booking

A user in `admins` may cancel any booking, including bookings owned by other users. Any other user who is not
the booking's owner gets `BookingError` from `cancel`, and the booking stays active.

Signed-off-by: Dana Okafor, Facilities Lead, 2026-10-30
