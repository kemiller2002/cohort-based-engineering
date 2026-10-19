One JSON file per run: `<arm>/<runId>.json`, valid against
`../schema/observation.schema.json`. Append only; a corrected run is a new
file whose `supersedes` names the old `runId`. Empty until runs are executed.
