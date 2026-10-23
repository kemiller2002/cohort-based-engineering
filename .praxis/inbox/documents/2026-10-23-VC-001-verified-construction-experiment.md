# VC-001: Verified construction versus post-hoc enforcement

## Goal
Evaluate a shift from repeated agent decision gates to provenance-backed, strongly typed construction while preserving four-tier engineering responsibilities.

## Evidence
VAC-002-P3: https://github.com/kemiller2002/cohort-based-engineering/pull/21 . All 36 confirmed unauthorized decisions reused code-embedded rules; executable authorization prevented none and caused false rejections. These results motivate, but do not establish, verified construction's effectiveness.

## Requirements
1. Preregister a four-arm comparison: A conventional TypeScript; B strict TypeScript with discriminated unions; C conventional F# domain modeling; D F# with verified-requirement/decision-provenance-driven construction. Ensure equivalent functionality and compiler/toolchain versions recorded.
2. Use at least two bounded domain fixtures including money-owed exemptions, unauthorized defaults, conflicting rules, state transitions and persistence permissions. Avoid a single easy ceiling-effect corpus. Qualify a discriminating baseline before treatment trials.
3. Freeze independent functional and authority oracles before runs; explicitly test whether source-code rules are improperly treated as policy authority.
4. Track unauthorized consequential decisions, valid acceptance, invalid transitions, compiler failures, repair iterations, false rejections, input/output/cached tokens, cost and wall time. Separate language effect (C vs B, with caveats) from construction-model effect (D vs C).
5. Include independent blinded review, paired trials, preregistered statistical analysis, sensitivity checks, and complete reproduction.
6. Begin with a small, budgeted pilot. No paid execution beyond an explicitly authorized spending ceiling. No production-default changes until evidence supports them.
7. Preserve the existing four-tier architecture and document each tier's responsibility. Do not silently redefine established tier contracts.

## Acceptance
Protocol, frozen fixtures, oracle validation, reproducible harness and bounded pilot report committed to research/experiments/VC-001/. Report limitations and all failure cases. No GitHub Issues.
