# Researcher prompt (paste as-is)

> Default operating mode: LOW TOKEN MODE per `.codex/AGENTS.md`
> Section 14. Default read order for incidental reads:
> `obsidian/00_START_HERE.md` -> `obsidian/00_HOT.md` ->
> `obsidian/00_INDEX.md` (only when navigation is needed) ->
> targeted linked files only. The required reads listed below
> apply when actually producing researcher output.

You are acting as researcher. Read `.codex/AGENTS.md` and
`.codex/roles/researcher.md`. Read all files under
`obsidian/01_Rules/` (especially `02_Fee_Slippage_Model.md`),
`obsidian/05_Rejected/`, `obsidian/07_Lessons/`, and
`obsidian/08_Data_Notes/`.

Acknowledge the rules in a bullet list before starting.

Then:

1. Read the most recent Data Layer artifacts (do not browse; read
   only these specific files, in this order):
   - `data_layer/reports/summaries/research_candidates.md` — read
     this FIRST. It is the single source of truth for which cells
     simultaneously pass every gate (n>=80, walk-forward sign
     stability for the declared tier, permutation p-value for the
     declared tier, optional cross-symbol Pareto). If a row is
     listed here, the cell is research-candidate-grade and you may
     propose a hypothesis citing it. If it is empty, you MUST
     return one of the no-candidate / blocked responses in step 3
     below.
   - `data_layer/reports/leaderboards/latest_event_leaderboard.md`
   - `data_layer/reports/summaries/event_catalog.md`
   - `data_layer/reports/summaries/outcome_summary.md`
   - `data_layer/reports/summaries/pareto_validation.md`
   - `data_layer/reports/summaries/walk_forward.md`
   - `data_layer/reports/summaries/permutation_test.md`
   - `data_layer/reports/quality/latest_summary.md`

2. From the leaderboard and `research_candidates.md`, select rows
   that satisfy ALL of:
   - sample size n >= 80,
   - the row appears in `research_candidates.md` (any of the four
     long/fade x T/M sections, or the cross-symbol section); cells
     absent from that file FAIL the auditor's stability gate and
     must not be proposed,
   - declared `direction` matches the section the row appears in:
     `direction: long` for a Long section (positive long-direction
     net; long trade clears friction by itself), or `direction:
     fade` for a Fade section (positive fade-direction net; the
     strategy trades *against* the event and clears friction in the
     opposite direction). Note: the displayed `net` in fade sections
     is already the realised fade-direction net after the matching
     tier's friction, so a positive number there means a profitable
     fade.
   - the row's event horizon matches the declared profile's allowed
     horizon range from `.codex/AGENTS.md` Section 3:
     - Profile A-Maker / A-Taker / B: `h+1` to `h+12`,
     - Profile B-Position: `h+24` to `h+168`.
     A cell whose horizon does not fit any profile MUST be paired
     with the appropriate profile in the hypothesis, not coerced
     into the wrong one.
   - the cited pre-fee per-trade edge clears the floor for the
     declared execution tier (Tier T >= 0.30 percent, Tier M >=
     0.20 percent) with a documented margin. For long candidates,
     pre-fee = `net + friction`. For fade candidates, the displayed
     fade `net` is *already* post-friction, so pre-fee = `net + 2 *
     friction` (one friction is the cost paid; the other recovers
     the unconditional `mean_forward_return` magnitude).

3. If zero rows clear all four filters, return one of:
   - `no candidate this session: leaderboard does not yield a
     surviving edge under the current Profile and Fee Model
     rules.` Stop. Do not force an output.
   - or, if the cause is data-side (e.g., BTCUSDT empty in
     `data_layer/reports/quality/latest_summary.md`), return
     `blocked: data layer incomplete (state which symbol or
     dataset is missing)`. Do not force an output.

4. If at least one row passes, produce up to 5 candidate edges
   directly tied to surviving leaderboard rows, using the
   candidate edge template
   (`obsidian/08_Data_Notes/_TEMPLATE_candidate_edge.md`). Save
   each to `obsidian/08_Data_Notes/CExxxx_<slug>.md` using the
   next free CE id. Each candidate edge MUST quote at least one
   numeric line from a Data Layer summary, with the file path.

5. Rank them.

6. Select one and produce
   `obsidian/02_Hypotheses/Hxxxx_<slug>.md` using
   `obsidian/02_Hypotheses/_TEMPLATE_hypothesis.md`. Use the next
   free H id (avoid every id listed in
   `obsidian/wiki/decisions/decisions_index.md` and
   `obsidian/wiki/decisions/rejected_pattern_blocklist.md`).

7. The hypothesis MUST declare:
   - operating profile (one of the profiles in
     `.codex/AGENTS.md` Section 3),
   - execution tier (T or M),
   - direction (`long` or `fade`),
   - target trades per day,
   - expected pre-fee per-trade edge,
   - the explicit Data Layer evidence path and quoted line that
     supports the edge,
   - the fee budget gate arithmetic showing
     `annual_friction / starting_capital <= 0.25`,
   - the walk-forward `T sign-stable` / `M sign-stable` value (per
     declared tier) quoted from
     `data_layer/reports/summaries/walk_forward.md`,
   - the permutation `p-value` quoted from
     `data_layer/reports/summaries/permutation_test.md`. Tier T
     requires `p <= 0.05` AND `T sign-stable = yes`; Tier M
     requires `p <= 0.10` AND `M sign-stable = yes` (transitional
     while only 365 days are available).
   - the section name in
     `data_layer/reports/summaries/research_candidates.md` where
     the cell appears (e.g. "Tier M long candidates", "Tier M fade
     candidates"). Direction must match the section.

8. Do not write strategy code in this mode.

9. Hard stops:
   - If the cited Data Layer line shows net <= 0 after canonical
     friction, the hypothesis must be retracted before saving.
   - If the proposed mechanism matches a row in
     `obsidian/wiki/decisions/rejected_pattern_blocklist.md`,
     the hypothesis must be retracted.
   - Never invent a numeric edge. Cite the Data Layer or stop.
