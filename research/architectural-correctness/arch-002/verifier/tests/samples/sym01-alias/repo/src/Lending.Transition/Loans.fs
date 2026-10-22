module Lending.Transition.Loans

open type Term

let exists (path: string) = Disk.Exists path

let announce (message: string) = WriteLine message
