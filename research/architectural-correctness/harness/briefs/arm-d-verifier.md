
## Architecture verifier

`archcheck` (on your PATH) checks the repository against the architecture rules mechanically. During
development run

    archcheck verify --repo {{REPO}} --policy {{POLICY}} --contract {{TOOLS}}/contracts/{{CONTRACT_FILE}}

and fix every DET violation it reports. `submit` also runs `archcheck verify` with this policy on the
committed HEAD and fails while any DET violation of severity 2 or higher remains.
