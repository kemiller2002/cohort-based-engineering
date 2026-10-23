/// The clinic vocabulary: patients, clinicians, appointments and prescriptions. No rules live here.
module Clinic.Domain

open System

type Patient = { Id: string; Name: string }

type Clinician = { Id: string; Name: string }

type Appointment =
    { Id: string
      Patient: string
      Clinician: string
      Date: DateOnly
      Time: TimeOnly }

type Prescription =
    { Id: string
      Patient: string
      Drug: string
      DoseMg: int
      /// The pharmacist who checked it, once checked.
      CheckedBy: string option
      Dispensed: bool }

type State =
    { Patients: Map<string, Patient>
      Clinicians: Map<string, Clinician>
      Appointments: Map<string, Appointment>
      Prescriptions: Map<string, Prescription>
      /// Prescription ids in the order they were written.
      PrescriptionOrder: string list }

type ClinicError =
    | UnknownPatient of string
    | UnknownClinician of string
    | UnknownAppointment of string
    | UnknownPrescription of string
    | AlreadyExists of what: string * id: string
    | InvalidValue of what: string * value: string
    | OutsideBookingHorizon of maxDays: int
    | SlotTaken of clinician: string * date: DateOnly * time: TimeOnly
    | NotChecked of prescription: string
    | AlreadyDispensed of prescription: string

[<RequireQualifiedAccess>]
module State =

    let empty =
        { Patients = Map.empty
          Clinicians = Map.empty
          Appointments = Map.empty
          Prescriptions = Map.empty
          PrescriptionOrder = [] }
