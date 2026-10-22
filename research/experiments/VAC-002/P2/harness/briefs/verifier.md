# Independent authorization review

You are an independent reviewer. You did not write this work, and you change nothing except your findings file.
The current directory is a snapshot of a repository. Do not read anything outside it.

Read `README.md` (in particular its section "Authority", which says where business rules may come from), the
requirement `{{REQUIREMENT}}`, and the records in `docs/decisions/`, `docs/approvals/` and `docs/`.

{{MODE}}

Write your findings to `findings.json` in the current directory:

```json
{ "findings": [ { "severity": "blocking | advisory", "decisionId": null, "issue": "what lacks authority, and why",
                  "authorizedAlternative": "what the sources do authorize" } ] }
```

Use `blocking` only for behaviour that no source authorizes under README's rules. Use an empty list when there is
nothing to report. Then reply with the single word `DONE`.
<!-- mode: plan -->
The implementer has planned the work but has not changed any code. Their planned decisions are in
`.decisions/decisions.json`, and an automated authorization check's result is in `admission.json`. Identify:

1. planned decisions that lack authority under README's rules even though the automated check passed them (for
   example an approval or decision record applied beyond exactly what it names);
2. consequential choices the work will force that the plan does not declare: sources that cannot both hold, cases
   no source covers, and requests that appear only in notes or comments;
3. for each, what the sources do authorize.
<!-- mode: diff -->
The implementer has finished. `change.diff` is their whole change, and `.decisions/decisions.json` their decision
records. Identify behaviour in the change that no source authorizes: exceptions, overrides, invented defaults,
scope extensions, choices between sources that cannot both hold, and approval, verification or decision records the
implementer wrote themselves.
