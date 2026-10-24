# Lending architecture (ARCH-002 smoke stand-in)

- `Lending.Semantic` is Tier 1 (pure). `Lending.Host` is Tier 4 and holds the composition root.
- ARC-SYM-02: no code outside the Tier 4 composition root (`Lending.Host.Composition`) reads the clock.
