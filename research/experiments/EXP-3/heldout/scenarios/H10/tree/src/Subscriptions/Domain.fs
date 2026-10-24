/// Subscription domain types. Data only; the rules live in Rules.fs.
module Subscriptions.Domain

open System

type Customer =
    { Id: string
      Email: string
      Country: string }

type Plan = { Code: string; Monthly: decimal }

type Subscription =
    { SubscriptionId: string
      Customer: Customer
      Plan: string
      Seats: int
      FirstCharged: DateOnly
      LastCharge: decimal
      CycleStart: DateOnly
      CycleEnd: DateOnly }

type PaymentAttempt =
    { ForSubscription: string
      At: DateTime
      Succeeded: bool }
