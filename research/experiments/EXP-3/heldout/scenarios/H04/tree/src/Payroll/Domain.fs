/// Payroll domain types. Data only; the rules live in Rules.fs.
module Payroll.Domain

open System

type PayBasis =
    | Hourly
    | Salaried

type Employee =
    { Id: string
      Name: string
      Basis: PayBasis
      HourlyRate: decimal
      AnnualSalary: decimal
      Hired: DateOnly
      UnionLocal: string option
      Grade: int
      OnUnpaidLeave: bool }

type Timesheet =
    { EmployeeId: string
      WeekStarting: DateOnly
      RegularHours: decimal
      HolidayHours: decimal }

type ExpenseClaim =
    { Id: string
      Submitter: Employee
      Kind: string
      Amount: decimal
      HasReceipt: bool
      Kilometres: float
      Days: int }

type ExpensePolicy =
    { RatePerKm: float
      DailyMealCap: decimal }
