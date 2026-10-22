# Lending (ARCH-002 brownfield smoke stand-in)

A two-project stand-in used only by `arch-002/harness/smoke.sh`. It already holds one architecture violation
(`Fees.stampedAt` reads the clock in Tier 1). Build: `dotnet build`. Test: `dotnet test`.
