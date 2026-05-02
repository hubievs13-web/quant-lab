# 00_INGEST_LOG

Append-only log of every external or internal source ingested into
`obsidian/wiki/`.

## Rules

1. Append-only. Never edit a prior line.
2. One line per ingest action.
3. If the same source is re-ingested, add a new line with status
   `superseded` and link the new summary path.
4. If a source is rejected as not worth summarizing, add a line with
   status `rejected` and a one-clause reason.
5. Do not paste source contents here. Paths and short reasons only.

## Format

```
YYYY-MM-DD | source_path | summary_path | status | reason
```

Status values:

- `ingested`    raw kept under `obsidian/raw/`, no summary yet.
- `summarized`  summary written under `obsidian/wiki/summaries/`.
- `superseded`  replaced by a newer summary; old line stays here.
- `rejected`    not summarized; reason mandatory.

## Entries

(no entries yet)
