
## Architecture verifier

`archcheck` (on your PATH) checks the repository against the architecture rules mechanically. The
repository already contained some violations when you received it; they are recorded in the baseline
report `{{TOOLS}}/baseline/start.report.json`, and archcheck marks them `preexisting`. During
development run

    archcheck verify --repo {{REPO}} --policy {{POLICY}} --contract {{TOOLS}}/contracts/{{CONTRACT_FILE}} --baseline {{TOOLS}}/baseline/start.report.json

and fix every new DET violation it reports. `submit` also runs `archcheck verify` with this policy and
baseline on the committed HEAD, and fails while any new DET violation of severity 2 or higher remains.
Pre-existing violations never fail `submit`; you do not have to fix them.
