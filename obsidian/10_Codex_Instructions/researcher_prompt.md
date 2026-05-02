# Researcher prompt (paste as-is)

> Default operating mode: LOW TOKEN MODE per `.codex/AGENTS.md`
> Section 14. Default read order for incidental reads:
> `obsidian/00_START_HERE.md` -> `obsidian/00_HOT.md` ->
> `obsidian/00_INDEX.md` (only when navigation is needed) ->
> targeted linked files only. The required reads listed below
> apply when actually producing researcher output.

You are acting as researcher. Read .codex/AGENTS.md and
.codex/roles/researcher.md. Read all files under obsidian/01_Rules/,
obsidian/05_Rejected/, obsidian/07_Lessons/, and obsidian/08_Data_Notes/.

Acknowledge the rules in a bullet list before starting.

Then:

1. Produce up to 5 candidate edges on Binance USD-M Futures using the
   candidate edge template
   (obsidian/08_Data_Notes/_TEMPLATE_candidate_edge.md). Save each to
   obsidian/08_Data_Notes/CExxxx_<slug>.md using the next free CE id.
2. Rank them.
3. Select one and produce obsidian/02_Hypotheses/Hxxxx_<slug>.md using
   obsidian/02_Hypotheses/_TEMPLATE_hypothesis.md. Use the next free H
   id (avoid H0001, H0003, H0004, H0006).
4. Do not write strategy code in this mode.
5. If no candidate clears the pre-fee edge floor >= 0.10 percent per
   trade a priori, return zero hypotheses. Do not force an output.
