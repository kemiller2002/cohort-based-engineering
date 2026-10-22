# OpenDays changelog

## 2.0.0 (2026-03-20)

- **Breaking:** `Calendar.nextOpen` now returns the first open day *after* the given day, matching the
  shared booking system. The previous behaviour (the given day when open) is `Calendar.onOrAfter`.
- Holidays for January and February 2027.

## 1.4.0 (2025-12-01)

- Holidays for 2026 and New Year 2027.

## 1.3.0 (2024-11-20)

- `Calendar.nextOpen` added: the given day when open, otherwise the next open day.

## 1.0.0 (2023-01-09)

- `Calendar.isOpen`, `Calendar.holidays`.
