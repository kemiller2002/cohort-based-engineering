# Agent brief

You are a software engineer working in `{{REPO}}`, a git repository holding `{{APP_NAME}}`, {{APP_DESCRIPTION}}
(`README.md` describes it).

## Task

{{TASK_LINE}}
Visible acceptance tests for it are in `{{ACCEPTANCE_DIR}}/`; they may not compile until the work is
done. Add or extend tests in `{{TESTS_DIR}}` as you see fit.

## Build and test

From the repository root: `dotnet build` and `dotnet test` (solution `{{SOLUTION}}`).

## Finishing: `submit`

When you believe the work is done, commit it (`git add -A && git commit -m "..."`), then run `submit`
(it is on your PATH). `submit` checks the committed HEAD: the working tree must be clean and committed;
it then builds the solution and runs the visible tests, plus any further checks named later in this
brief, and prints PASS or FAIL with the reasons.

- If `submit` prints FAIL, fix the causes, commit, and run `submit` again.
- You may run `submit` at most {{MAX_SUBMITS}} times. Stop as soon as `submit` prints PASS, or after
  the {{MAX_SUBMITS_ORDINAL}} `submit`, whatever it printed.

## Limits

- Time budget: {{BUDGET_MINUTES}} minutes of wall-clock time from your first command.
- Keep the solution's project structure: do not add, remove or rename projects (`.fsproj` files).
- Work only inside `{{REPO}}`. Do not modify anything under `{{TOOLS}}`. No network access, and no
  package installs beyond restoring the packages already referenced.

## Final message

End your final message with exactly one line `ARCH002-DONE <gitHead>`, where `<gitHead>` is the output
of `git rev-parse HEAD` at the end of your work.
