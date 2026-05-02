# QCERR-xxxx: <short slug>

One QuantConnect / Lean error. Append-only log of occurrences and
resolutions. Hard cap: ~80 lines.

## Symptom

Exact log substring (one line preferred). Use a fenced code block:

```
<paste exact log line here>
```

## Lean version

- Engine: v17685.
- QC project: 30774195.

## Status

- `open` | `resolved` | `known-limitation`.

## First seen

- date: YYYY-MM-DD
- backtest: BTxxxx
- hypothesis: Hxxxx
- log file: `<path>`

## Root cause

Short, technical, no theory.

## Confirmed fix or workaround

Numbered steps. If the user has not confirmed, mark "unconfirmed".

## Forbidden follow-ups

- Do not retry by tuning parameters of a rejected hypothesis.
- Other constraints specific to this error.

## Pattern link

- Related pattern: `obsidian/wiki/qc_lean/patterns/<file>.md` (if
  any).

## Occurrences (append-only)

- YYYY-MM-DD | BTxxxx | Hxxxx | `<log path>` | notes
- (append; never edit prior lines)

## Resolution log (append-only)

- YYYY-MM-DD | who confirmed | what fix worked
- (append; never edit prior lines)

## Verdict touch

- Does not change any verdict.
- Does not authorize tuning.
