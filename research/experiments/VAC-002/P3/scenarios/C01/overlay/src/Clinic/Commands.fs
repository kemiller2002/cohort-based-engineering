/// State transitions. Each command takes the current state and returns the next state and its output, or an error.
/// Commands decide nothing on their own: every clinic rule comes from `Rules`.
module Clinic.Commands

open System
open System.Globalization
open Clinic.Domain

let date (day: DateOnly) = day.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture)

let time (t: TimeOnly) = t.ToString("HH:mm", CultureInfo.InvariantCulture)

let private found (error: ClinicError) (value: 'a option) =
    match value with
    | Some v -> Ok v
    | None -> Error error

let parseDate (text: string) =
    match DateOnly.TryParseExact(text, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None) with
    | true, d -> Ok d
    | _ -> Error(InvalidValue("date", text))

let parseTime (text: string) =
    match TimeOnly.TryParseExact(text, "HH:mm", CultureInfo.InvariantCulture, DateTimeStyles.None) with
    | true, t -> Ok t
    | _ -> Error(InvalidValue("time", text))

let parseDose (text: string) =
    match Int32.TryParse(text, NumberStyles.None, CultureInfo.InvariantCulture) with
    | true, dose when dose > 0 -> Ok dose
    | _ -> Error(InvalidValue("dose", text))

let addPatient (id: string) (name: string) (state: State) =
    if state.Patients.ContainsKey id then
        Error(AlreadyExists("patient", id))
    else
        Ok({ state with Patients = state.Patients |> Map.add id { Id = id; Name = name } }, $"patient {id} added: {name}")

let addClinician (id: string) (name: string) (state: State) =
    if state.Clinicians.ContainsKey id then
        Error(AlreadyExists("clinician", id))
    else
        Ok(
            { state with Clinicians = state.Clinicians |> Map.add id { Id = id; Name = name } },
            $"clinician {id} added: {name}"
        )

let book (today: DateOnly) (id: string) (patient: string) (clinician: string) (day: DateOnly) (at: TimeOnly) (state: State) =
    state.Patients |> Map.tryFind patient |> found (UnknownPatient patient)
    |> Result.bind (fun _ -> state.Clinicians |> Map.tryFind clinician |> found (UnknownClinician clinician))
    |> Result.bind (fun _ ->
        if state.Appointments.ContainsKey id then Error(AlreadyExists("appointment", id))
        elif not (Rules.withinBookingHorizon today day) then Error(OutsideBookingHorizon Rules.bookingHorizonDays)
        elif not (Rules.slotFree state clinician day at) then Error(SlotTaken(clinician, day, at))
        else
            let booked =
                { Id = id
                  Patient = patient
                  Clinician = clinician
                  Date = day
                  Time = at }

            Ok(
                { state with Appointments = state.Appointments |> Map.add id booked },
                $"{id} booked: {patient} with {clinician} on {date day} at {time at}"
            ))

let cancel (id: string) (state: State) =
    state.Appointments |> Map.tryFind id |> found (UnknownAppointment id)
    |> Result.map (fun _ -> { state with Appointments = state.Appointments |> Map.remove id }, $"{id} cancelled")

let schedule (clinician: string) (day: DateOnly) (state: State) =
    state.Clinicians |> Map.tryFind clinician |> found (UnknownClinician clinician)
    |> Result.map (fun _ ->
        let entries =
            state.Appointments
            |> Map.toList
            |> List.map snd
            |> List.filter (fun a -> a.Clinician = clinician && a.Date = day)
            |> List.sortBy (fun a -> a.Time, a.Id)
            |> List.map (fun a -> $"{time a.Time} {a.Id} {a.Patient}")

        let listing = if List.isEmpty entries then "none" else String.Join(", ", entries)
        state, $"{clinician} on {date day}: {listing}")

let reminder (id: string) (state: State) =
    state.Appointments |> Map.tryFind id |> found (UnknownAppointment id)
    |> Result.map (fun a ->
        let at = Rules.reminderAt a
        state, $"{id} reminder at {date (DateOnly.FromDateTime at)} {time (TimeOnly.FromDateTime at)}")

let prescribe (id: string) (patient: string) (drug: string) (dose: int) (state: State) =
    state.Patients |> Map.tryFind patient |> found (UnknownPatient patient)
    |> Result.bind (fun _ ->
        if state.Prescriptions.ContainsKey id then
            Error(AlreadyExists("prescription", id))
        else
            let written =
                { Id = id
                  Patient = patient
                  Drug = drug
                  DoseMg = dose
                  CheckedBy = None
                  Dispensed = false }

            Ok(
                { state with
                    Prescriptions = state.Prescriptions |> Map.add id written
                    PrescriptionOrder = state.PrescriptionOrder @ [ id ] },
                $"{id} prescribed: {drug} {dose} mg for {patient}"
            ))

let private prescription (id: string) (state: State) =
    state.Prescriptions |> Map.tryFind id |> found (UnknownPrescription id)

let private replace (rx: Prescription) (state: State) =
    { state with Prescriptions = state.Prescriptions |> Map.add rx.Id rx }

let check (id: string) (pharmacist: string) (state: State) =
    prescription id state
    |> Result.map (fun rx -> replace { rx with CheckedBy = Some pharmacist } state, $"{id} checked by {pharmacist}")

let dispense (id: string) (state: State) =
    prescription id state
    |> Result.bind (fun rx ->
        if rx.Dispensed then Error(AlreadyDispensed id)
        elif not (Rules.mayDispense rx) then Error(NotChecked id)
        else Ok(replace { rx with Dispensed = true } state, $"{id} dispensed"))

let queue (state: State) =
    let waiting =
        state.PrescriptionOrder
        |> List.map (fun id -> state.Prescriptions[id])
        |> List.filter (fun rx -> not rx.Dispensed)
        |> List.map (fun rx -> sprintf "%s (%s)" rx.Id (if rx.CheckedBy.IsSome then "checked" else "unchecked"))

    Ok(state, (if List.isEmpty waiting then "queue: empty" else "queue: " + String.Join(", ", waiting)))

let describeError (error: ClinicError) =
    match error with
    | UnknownPatient id -> $"unknown patient {id}"
    | UnknownClinician id -> $"unknown clinician {id}"
    | UnknownAppointment id -> $"unknown appointment {id}"
    | UnknownPrescription id -> $"unknown prescription {id}"
    | AlreadyExists(what, id) -> $"{what} {id} already exists"
    | InvalidValue(what, value) -> $"invalid {what} {value}"
    | OutsideBookingHorizon days -> $"appointments can be booked 1 to {days} days ahead"
    | SlotTaken(clinician, day, at) -> $"{clinician} is already booked on {date day} at {time at}"
    | NotChecked id -> $"{id} has not been checked by a pharmacist"
    | AlreadyDispensed id -> $"{id} has already been dispensed"
