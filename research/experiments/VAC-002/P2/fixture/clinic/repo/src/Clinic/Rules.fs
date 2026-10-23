/// Clinic rules, each traced to the decision record that sets it (docs/decisions/). Pure functions only.
module Clinic.Rules

open System
open Clinic.Domain

/// DEC-C01: appointments are booked from tomorrow up to 90 days ahead.
let bookingHorizonDays = 90

let withinBookingHorizon (today: DateOnly) (date: DateOnly) =
    date > today && date <= today.AddDays bookingHorizonDays

/// DEC-C02: a clinician has at most one appointment at a given date and time.
let slotFree (state: State) (clinician: string) (date: DateOnly) (time: TimeOnly) =
    state.Appointments
    |> Map.forall (fun _ a -> not (a.Clinician = clinician && a.Date = date && a.Time = time))

/// DEC-C03: a prescription is dispensed only after a pharmacist has checked it.
let mayDispense (prescription: Prescription) = prescription.CheckedBy.IsSome && not prescription.Dispensed
