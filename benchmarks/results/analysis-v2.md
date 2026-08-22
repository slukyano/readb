# Benchmark results — v2

702 runs recorded, 0 excluded as invalid, 702 used.
Models: claude-haiku-4-5, claude-sonnet-5. Arms: baseline, readb-bare, readb-nudged, readb-skill, shell-coached. Questions: 26.

## Pre-registered endpoints

| id | contrast | model | questions | effect | p | Holm p | test |
|---|---|---|---|---|---|---|---|
| E1 | readb-bare vs shell-coached, billed cost, join stratum | sonnet-5 | 8 | 0.74x [0.66–1.41] | 0.4609 | 1.0000 | exact (256 sign assignments) |
| E2 | readb-bare vs shell-coached, billed cost, backlog stratum | sonnet-5 | 8 | 1.02x [0.88–1.30] | 0.4609 | 1.0000 | exact (256 sign assignments) |
| E3 | readb-bare vs shell-coached, exactness, every question | haiku-4-5 | 26 | 92% vs 92%  | — | — | too few pairs |

- **E1** — the eight questions where v1's per-question effect was largest.
- **E2** — recorded in advance: that bundle is small, so runs sit near the harness floor and a compressed ratio is the expected honest outcome. Parity is a finding.
- **E3** — the accuracy dimension has variance on a weaker model, where v1 had none.

## claude-haiku-4-5

### Per arm, all questions pooled

| arm | n | exact | partial | answer parsed | cost, as billed (USD) | new tokens ingested | turns | cumulative prompt tokens |
|---|---|---|---|---|---|---|---|---|
| baseline | 78 | 77% | 0.84 | 100% | 0.0492 | 10,883 | 8.0 | 202,430 |
| readb-bare | 78 | 92% | 0.93 | 100% | 0.0322 | 8,527 | 4.0 | 94,528 |
| readb-nudged | 78 | 94% | 0.94 | 100% | 0.0281 | 8,366 | 3.0 | 70,730 |
| shell-coached | 78 | 92% | 0.93 | 100% | 0.0291 | 8,298 | 4.0 | 93,179 |

### Ratio to `baseline`, paired by question (below 1.00 favours the arm)

| arm | cost, as billed (USD) [95% CI] | new tokens ingested [95% CI] | turns [95% CI] | cumulative prompt tokens [95% CI] |
|---|---|---|---|---|
| readb-bare | 0.75x [0.57–0.89] | 0.89x [0.78–0.97] | 0.54x [0.46–0.92] | 0.57x [0.45–0.83] |
| readb-nudged | 0.60x [0.49–0.88] | 0.85x [0.70–1.01] | 0.50x [0.37–0.64] | 0.47x [0.30–0.69] |
| readb-skill | — | — | — | — |
| shell-coached | 0.69x [0.55–0.78] | 0.82x [0.76–0.91] | 0.56x [0.42–0.71] | 0.52x [0.38–0.68] |

### Billed-cost ratio to `baseline` by stratum

| arm | backlog (n=8) | hazard (n=3) | join (n=8) | retrieval (n=3) | scan (n=4) |
|---|---|---|---|---|---|
| readb-bare | 0.89x | 0.79x | 0.38x | 0.99x | 0.68x |
| readb-nudged | 0.66x | 0.89x | 0.38x | 1.24x | 0.71x |
| readb-skill | — | — | — | — | — |
| shell-coached | 0.74x | 0.80x | 0.50x | 1.00x | 0.74x |

### Tool choice — what the agent reached for, against what a question declares

A result, never a reason to edit a prompt. `match` is the share of runs whose chosen tool equalled the question's declared expert tool.

| arm | readb | shell | read | other | none | match | failed calls | failed readb |
|---|---|---|---|---|---|---|---|---|
| baseline | 0 | 73 | 5 | 0 | 0 | 17% | 53 | 0 |
| readb-bare | 62 | 13 | 3 | 0 | 0 | 78% | 23 | 7 |
| readb-nudged | 71 | 7 | 0 | 0 | 0 | 74% | 25 | 13 |
| shell-coached | 0 | 70 | 8 | 0 | 0 | 23% | 25 | 0 |

### The nudge — `readb-nudged` against `readb-bare`

| measure | readb-bare | readb-nudged |
|---|---|---|
| exact | 92% | 94% |
| tool match | 78% | 74% |
| readb reached for | 79% | 91% |
| billed cost (median) | 0.0322 | 0.0281 |
| turns (median) | 4.0 | 3.0 |

Paired cost ratio, nudged/bare: **0.98x** over 26 questions, p = 0.1099 (Monte Carlo (200,000 sign flips, seed 24)).

## claude-sonnet-5

### Per arm, all questions pooled

| arm | n | exact | partial | answer parsed | cost, as billed (USD) | new tokens ingested | turns | cumulative prompt tokens |
|---|---|---|---|---|---|---|---|---|
| baseline | 78 | 85% | 0.91 | 100% | 0.0914 | 11,778 | 6.0 | 184,862 |
| readb-bare | 78 | 97% | 0.98 | 100% | 0.0679 | 10,175 | 4.0 | 122,803 |
| readb-nudged | 78 | 100% | 1.00 | 100% | 0.0668 | 10,152 | 4.0 | 122,216 |
| readb-skill | 78 | 96% | 0.99 | 100% | 0.0792 | 12,384 | 5.0 | 132,146 |
| shell-coached | 78 | 97% | 0.97 | 100% | 0.0702 | 10,288 | 3.0 | 100,626 |

### Ratio to `baseline`, paired by question (below 1.00 favours the arm)

| arm | cost, as billed (USD) [95% CI] | new tokens ingested [95% CI] | turns [95% CI] | cumulative prompt tokens [95% CI] |
|---|---|---|---|---|
| readb-bare | 0.72x [0.62–0.95] | 0.85x [0.71–1.02] | 0.70x [0.50–1.00] | 0.66x [0.50–1.00] |
| readb-nudged | 0.70x [0.54–0.92] | 0.85x [0.70–1.02] | 0.69x [0.48–1.00] | 0.64x [0.45–1.00] |
| readb-skill | 0.87x [0.74–1.02] | 1.01x [0.91–1.06] | 1.00x [0.75–1.00] | 0.86x [0.69–1.00] |
| shell-coached | 0.75x [0.71–0.85] | 0.87x [0.86–0.90] | 0.69x [0.57–0.79] | 0.66x [0.52–0.78] |

### Billed-cost ratio to `baseline` by stratum

| arm | backlog (n=8) | hazard (n=3) | join (n=8) | retrieval (n=3) | scan (n=4) |
|---|---|---|---|---|---|
| readb-bare | 0.90x | 0.69x | 0.60x | 1.02x | 0.72x |
| readb-nudged | 0.85x | 0.56x | 0.57x | 1.02x | 0.63x |
| readb-skill | 1.02x | 0.68x | 0.80x | 1.01x | 0.88x |
| shell-coached | 0.83x | 0.74x | 0.71x | 0.86x | 0.59x |

### Tool choice — what the agent reached for, against what a question declares

A result, never a reason to edit a prompt. `match` is the share of runs whose chosen tool equalled the question's declared expert tool.

| arm | readb | shell | read | other | none | match | failed calls | failed readb |
|---|---|---|---|---|---|---|---|---|
| baseline | 0 | 77 | 1 | 0 | 0 | 15% | 48 | 0 |
| readb-bare | 65 | 13 | 0 | 0 | 0 | 78% | 11 | 8 |
| readb-nudged | 68 | 10 | 0 | 0 | 0 | 79% | 20 | 19 |
| readb-skill | 37 | 39 | 2 | 0 | 0 | 47% | 25 | 7 |
| shell-coached | 0 | 77 | 1 | 0 | 0 | 17% | 10 | 0 |

### The nudge — `readb-nudged` against `readb-bare`

| measure | readb-bare | readb-nudged |
|---|---|---|
| exact | 97% | 100% |
| tool match | 78% | 79% |
| readb reached for | 83% | 87% |
| billed cost (median) | 0.0679 | 0.0668 |
| turns (median) | 4.0 | 4.0 |

Paired cost ratio, nudged/bare: **1.00x** over 26 questions, p = 0.1969 (Monte Carlo (200,000 sign flips, seed 24)).

## The malformed-file hazard

`saw warning` counts runs where readb's skip warning reached the transcript. A wrong answer with the warning seen and a wrong answer without it are different findings: the first says the warning did not work, the second says the hazard is silent.

| model | arm | question | n | exact | saw warning | tool |
|---|---|---|---|---|---|---|
| haiku-4-5 | baseline | q10 | 3 | 100% | 0/3 | shell |
| haiku-4-5 | baseline | q10b | 3 | 100% | 0/3 | shell |
| haiku-4-5 | baseline | q18 | 3 | 33% | 0/3 | shell |
| haiku-4-5 | readb-bare | q10 | 3 | 100% | 0/3 | shell |
| haiku-4-5 | readb-bare | q10b | 3 | 100% | 2/3 | readb/shell |
| haiku-4-5 | readb-bare | q18 | 3 | 0% | 3/3 | readb |
| haiku-4-5 | readb-nudged | q10 | 3 | 100% | 0/3 | shell |
| haiku-4-5 | readb-nudged | q10b | 3 | 100% | 3/3 | readb |
| haiku-4-5 | readb-nudged | q18 | 3 | 0% | 3/3 | readb |
| haiku-4-5 | shell-coached | q10 | 3 | 100% | 0/3 | shell |
| haiku-4-5 | shell-coached | q10b | 3 | 100% | 0/3 | shell |
| haiku-4-5 | shell-coached | q18 | 3 | 0% | 0/3 | shell |
| sonnet-5 | baseline | q10 | 3 | 100% | 0/3 | shell |
| sonnet-5 | baseline | q10b | 3 | 100% | 0/3 | shell |
| sonnet-5 | baseline | q18 | 3 | 67% | 0/3 | shell |
| sonnet-5 | readb-bare | q10 | 3 | 100% | 0/3 | shell |
| sonnet-5 | readb-bare | q10b | 3 | 100% | 3/3 | readb |
| sonnet-5 | readb-bare | q18 | 3 | 100% | 3/3 | readb |
| sonnet-5 | readb-nudged | q10 | 3 | 100% | 0/3 | shell |
| sonnet-5 | readb-nudged | q10b | 3 | 100% | 3/3 | readb |
| sonnet-5 | readb-nudged | q18 | 3 | 100% | 3/3 | readb |
| sonnet-5 | readb-skill | q10 | 3 | 100% | 0/3 | shell |
| sonnet-5 | readb-skill | q10b | 3 | 100% | 3/3 | readb |
| sonnet-5 | readb-skill | q18 | 3 | 100% | 3/3 | readb |
| sonnet-5 | shell-coached | q10 | 3 | 100% | 0/3 | shell |
| sonnet-5 | shell-coached | q10b | 3 | 100% | 0/3 | shell |
| sonnet-5 | shell-coached | q18 | 3 | 100% | 0/3 | shell |

## By question

| question | stratum | shape | expert | model | arm | n | exact | ingested | cost (billed) | turns | readb calls |
|---|---|---|---|---|---|---|---|---|---|---|---|
| b1 | backlog | ready-to-schedule | readb | haiku-4-5 | baseline | 3 | 33% | 16,311 | 0.0951 | 12.0 | 0.0 |
| b1 | backlog | ready-to-schedule | readb | haiku-4-5 | readb-bare | 3 | 100% | 9,013 | 0.0387 | 4.0 | 3.0 |
| b1 | backlog | ready-to-schedule | readb | haiku-4-5 | readb-nudged | 3 | 100% | 9,533 | 0.0407 | 4.0 | 3.0 |
| b1 | backlog | ready-to-schedule | readb | haiku-4-5 | shell-coached | 3 | 100% | 13,354 | 0.0692 | 8.0 | 0.0 |
| b1 | backlog | ready-to-schedule | readb | sonnet-5 | baseline | 3 | 100% | 18,154 | 0.1837 | 12.0 | 0.0 |
| b1 | backlog | ready-to-schedule | readb | sonnet-5 | readb-bare | 3 | 100% | 14,923 | 0.1003 | 4.0 | 3.0 |
| b1 | backlog | ready-to-schedule | readb | sonnet-5 | readb-nudged | 3 | 100% | 14,749 | 0.0929 | 3.0 | 2.0 |
| b1 | backlog | ready-to-schedule | readb | sonnet-5 | readb-skill | 3 | 100% | 18,540 | 0.1551 | 10.0 | 3.0 |
| b1 | backlog | ready-to-schedule | readb | sonnet-5 | shell-coached | 3 | 100% | 14,280 | 0.0773 | 2.0 | 0.0 |
| b2 | backlog | active sprint scope + design approach | readb | haiku-4-5 | baseline | 3 | 100% | 9,806 | 0.0445 | 8.0 | 0.0 |
| b2 | backlog | active sprint scope + design approach | readb | haiku-4-5 | readb-bare | 3 | 100% | 9,556 | 0.0397 | 10.0 | 2.0 |
| b2 | backlog | active sprint scope + design approach | readb | haiku-4-5 | readb-nudged | 3 | 100% | 9,619 | 0.0392 | 10.0 | 2.0 |
| b2 | backlog | active sprint scope + design approach | readb | haiku-4-5 | shell-coached | 3 | 100% | 9,425 | 0.0432 | 8.0 | 0.0 |
| b2 | backlog | active sprint scope + design approach | readb | sonnet-5 | baseline | 3 | 100% | 11,518 | 0.0883 | 6.0 | 0.0 |
| b2 | backlog | active sprint scope + design approach | readb | sonnet-5 | readb-bare | 3 | 100% | 10,149 | 0.0676 | 4.0 | 3.0 |
| b2 | backlog | active sprint scope + design approach | readb | sonnet-5 | readb-nudged | 3 | 100% | 10,310 | 0.0680 | 4.0 | 3.0 |
| b2 | backlog | active sprint scope + design approach | readb | sonnet-5 | readb-skill | 3 | 100% | 13,245 | 0.1169 | 8.0 | 0.0 |
| b2 | backlog | active sprint scope + design approach | readb | sonnet-5 | shell-coached | 3 | 100% | 10,327 | 0.0741 | 5.0 | 0.0 |
| b3 | backlog | delivered from a finished sprint | readb | haiku-4-5 | baseline | 3 | 67% | 12,187 | 0.0634 | 12.0 | 0.0 |
| b3 | backlog | delivered from a finished sprint | readb | haiku-4-5 | readb-bare | 3 | 100% | 11,336 | 0.0562 | 11.0 | 3.0 |
| b3 | backlog | delivered from a finished sprint | readb | haiku-4-5 | readb-nudged | 3 | 100% | 8,079 | 0.0293 | 4.0 | 3.0 |
| b3 | backlog | delivered from a finished sprint | readb | haiku-4-5 | shell-coached | 3 | 100% | 9,335 | 0.0408 | 7.0 | 0.0 |
| b3 | backlog | delivered from a finished sprint | readb | sonnet-5 | baseline | 3 | 100% | 9,149 | 0.0627 | 4.0 | 0.0 |
| b3 | backlog | delivered from a finished sprint | readb | sonnet-5 | readb-bare | 3 | 100% | 9,599 | 0.0723 | 5.0 | 1.0 |
| b3 | backlog | delivered from a finished sprint | readb | sonnet-5 | readb-nudged | 3 | 100% | 9,693 | 0.0580 | 3.0 | 3.0 |
| b3 | backlog | delivered from a finished sprint | readb | sonnet-5 | readb-skill | 3 | 100% | 9,036 | 0.0557 | 3.0 | 0.0 |
| b3 | backlog | delivered from a finished sprint | readb | sonnet-5 | shell-coached | 3 | 100% | 9,458 | 0.0640 | 4.0 | 0.0 |
| b4 | backlog | open work touching a feature | readb | haiku-4-5 | baseline | 3 | 100% | 11,016 | 0.0496 | 6.0 | 0.0 |
| b4 | backlog | open work touching a feature | readb | haiku-4-5 | readb-bare | 3 | 67% | 9,117 | 0.0364 | 5.0 | 2.0 |
| b4 | backlog | open work touching a feature | readb | haiku-4-5 | readb-nudged | 3 | 100% | 7,738 | 0.0253 | 3.0 | 2.0 |
| b4 | backlog | open work touching a feature | readb | haiku-4-5 | shell-coached | 3 | 100% | 7,901 | 0.0270 | 3.0 | 0.0 |
| b4 | backlog | open work touching a feature | readb | sonnet-5 | baseline | 3 | 100% | 11,766 | 0.0968 | 6.0 | 0.0 |
| b4 | backlog | open work touching a feature | readb | sonnet-5 | readb-bare | 3 | 100% | 9,707 | 0.0654 | 4.0 | 3.0 |
| b4 | backlog | open work touching a feature | readb | sonnet-5 | readb-nudged | 3 | 100% | 9,710 | 0.0587 | 3.0 | 3.0 |
| b4 | backlog | open work touching a feature | readb | sonnet-5 | readb-skill | 3 | 100% | 12,508 | 0.0996 | 7.0 | 0.0 |
| b4 | backlog | open work touching a feature | readb | sonnet-5 | shell-coached | 3 | 100% | 10,550 | 0.0744 | 4.0 | 0.0 |
| b5 | backlog | single-task lookup | read | haiku-4-5 | baseline | 3 | 100% | 8,183 | 0.0273 | 4.0 | 0.0 |
| b5 | backlog | single-task lookup | read | haiku-4-5 | readb-bare | 3 | 100% | 8,638 | 0.0376 | 7.0 | 4.0 |
| b5 | backlog | single-task lookup | read | haiku-4-5 | readb-nudged | 3 | 100% | 8,381 | 0.0340 | 6.0 | 5.0 |
| b5 | backlog | single-task lookup | read | haiku-4-5 | shell-coached | 3 | 100% | 7,803 | 0.0271 | 4.0 | 0.0 |
| b5 | backlog | single-task lookup | read | sonnet-5 | baseline | 3 | 100% | 8,726 | 0.0533 | 3.0 | 0.0 |
| b5 | backlog | single-task lookup | read | sonnet-5 | readb-bare | 3 | 100% | 9,028 | 0.0549 | 3.0 | 1.0 |
| b5 | backlog | single-task lookup | read | sonnet-5 | readb-nudged | 3 | 100% | 10,007 | 0.0723 | 5.0 | 4.0 |
| b5 | backlog | single-task lookup | read | sonnet-5 | readb-skill | 3 | 100% | 8,828 | 0.0536 | 3.0 | 0.0 |
| b5 | backlog | single-task lookup | read | sonnet-5 | shell-coached | 3 | 100% | 9,176 | 0.0619 | 4.0 | 0.0 |
| b6 | backlog | dropped-task digest | readb | haiku-4-5 | baseline | 3 | 67% | 11,916 | 0.0583 | 10.0 | 0.0 |
| b6 | backlog | dropped-task digest | readb | haiku-4-5 | readb-bare | 3 | 100% | 8,193 | 0.0277 | 3.0 | 2.0 |
| b6 | backlog | dropped-task digest | readb | haiku-4-5 | readb-nudged | 3 | 100% | 8,208 | 0.0270 | 3.0 | 2.0 |
| b6 | backlog | dropped-task digest | readb | haiku-4-5 | shell-coached | 3 | 67% | 11,461 | 0.0600 | 10.0 | 0.0 |
| b6 | backlog | dropped-task digest | readb | sonnet-5 | baseline | 3 | 0% | 9,285 | 0.0578 | 3.0 | 0.0 |
| b6 | backlog | dropped-task digest | readb | sonnet-5 | readb-bare | 3 | 100% | 10,405 | 0.0683 | 4.0 | 3.0 |
| b6 | backlog | dropped-task digest | readb | sonnet-5 | readb-nudged | 3 | 100% | 10,064 | 0.0601 | 3.0 | 2.0 |
| b6 | backlog | dropped-task digest | readb | sonnet-5 | readb-skill | 3 | 33% | 10,416 | 0.0850 | 6.0 | 0.0 |
| b6 | backlog | dropped-task digest | readb | sonnet-5 | shell-coached | 3 | 100% | 10,249 | 0.0793 | 5.0 | 0.0 |
| b7 | backlog | next free number | readb | haiku-4-5 | baseline | 3 | 0% | 8,130 | 0.0282 | 4.0 | 0.0 |
| b7 | backlog | next free number | readb | haiku-4-5 | readb-bare | 3 | 33% | 7,839 | 0.0265 | 4.0 | 0.0 |
| b7 | backlog | next free number | readb | haiku-4-5 | readb-nudged | 3 | 33% | 7,397 | 0.0231 | 3.0 | 0.0 |
| b7 | backlog | next free number | readb | haiku-4-5 | shell-coached | 3 | 67% | 7,276 | 0.0214 | 2.0 | 0.0 |
| b7 | backlog | next free number | readb | sonnet-5 | baseline | 3 | 33% | 10,597 | 0.0697 | 4.0 | 0.0 |
| b7 | backlog | next free number | readb | sonnet-5 | readb-bare | 3 | 67% | 13,725 | 0.0823 | 4.0 | 1.0 |
| b7 | backlog | next free number | readb | sonnet-5 | readb-nudged | 3 | 100% | 12,036 | 0.0812 | 5.0 | 4.0 |
| b7 | backlog | next free number | readb | sonnet-5 | readb-skill | 3 | 100% | 12,371 | 0.0855 | 5.0 | 0.0 |
| b7 | backlog | next free number | readb | sonnet-5 | shell-coached | 3 | 100% | 9,166 | 0.0573 | 3.0 | 0.0 |
| b8 | backlog | tag rollup | readb | haiku-4-5 | baseline | 3 | 0% | 8,907 | 0.0391 | 6.0 | 0.0 |
| b8 | backlog | tag rollup | readb | haiku-4-5 | readb-bare | 3 | 100% | 10,306 | 0.0454 | 7.0 | 7.0 |
| b8 | backlog | tag rollup | readb | haiku-4-5 | readb-nudged | 3 | 100% | 9,173 | 0.0404 | 7.0 | 6.0 |
| b8 | backlog | tag rollup | readb | haiku-4-5 | shell-coached | 3 | 67% | 7,298 | 0.0214 | 2.0 | 0.0 |
| b8 | backlog | tag rollup | readb | sonnet-5 | baseline | 3 | 67% | 20,022 | 0.1703 | 11.0 | 0.0 |
| b8 | backlog | tag rollup | readb | sonnet-5 | readb-bare | 3 | 100% | 9,443 | 0.0576 | 3.0 | 2.0 |
| b8 | backlog | tag rollup | readb | sonnet-5 | readb-nudged | 3 | 100% | 9,808 | 0.0736 | 5.0 | 5.0 |
| b8 | backlog | tag rollup | readb | sonnet-5 | readb-skill | 3 | 100% | 12,073 | 0.0767 | 5.0 | 2.0 |
| b8 | backlog | tag rollup | readb | sonnet-5 | shell-coached | 3 | 33% | 8,826 | 0.0473 | 2.0 | 0.0 |
| q1 | scan | type rollup | readb | haiku-4-5 | baseline | 3 | 100% | 9,101 | 0.0379 | 6.0 | 0.0 |
| q1 | scan | type rollup | readb | haiku-4-5 | readb-bare | 3 | 100% | 7,947 | 0.0256 | 3.0 | 2.0 |
| q1 | scan | type rollup | readb | haiku-4-5 | readb-nudged | 3 | 100% | 7,789 | 0.0244 | 3.0 | 2.0 |
| q1 | scan | type rollup | readb | haiku-4-5 | shell-coached | 3 | 100% | 7,964 | 0.0284 | 4.0 | 0.0 |
| q1 | scan | type rollup | readb | sonnet-5 | baseline | 3 | 67% | 9,883 | 0.0615 | 3.0 | 0.0 |
| q1 | scan | type rollup | readb | sonnet-5 | readb-bare | 3 | 100% | 10,209 | 0.0681 | 4.0 | 5.0 |
| q1 | scan | type rollup | readb | sonnet-5 | readb-nudged | 3 | 100% | 10,452 | 0.0696 | 4.0 | 5.0 |
| q1 | scan | type rollup | readb | sonnet-5 | readb-skill | 3 | 100% | 12,016 | 0.0763 | 5.0 | 3.0 |
| q1 | scan | type rollup | readb | sonnet-5 | shell-coached | 3 | 100% | 8,947 | 0.0547 | 3.0 | 0.0 |
| q10 | hazard | malformed-file honesty, warned | shell | haiku-4-5 | baseline | 3 | 100% | 8,549 | 0.0363 | 3.0 | 0.0 |
| q10 | hazard | malformed-file honesty, warned | shell | haiku-4-5 | readb-bare | 3 | 100% | 8,174 | 0.0328 | 4.0 | 0.0 |
| q10 | hazard | malformed-file honesty, warned | shell | haiku-4-5 | readb-nudged | 3 | 100% | 8,703 | 0.0324 | 2.0 | 0.0 |
| q10 | hazard | malformed-file honesty, warned | shell | haiku-4-5 | shell-coached | 3 | 100% | 8,394 | 0.0292 | 3.0 | 0.0 |
| q10 | hazard | malformed-file honesty, warned | shell | sonnet-5 | baseline | 3 | 100% | 13,910 | 0.0886 | 4.0 | 0.0 |
| q10 | hazard | malformed-file honesty, warned | shell | sonnet-5 | readb-bare | 3 | 100% | 9,427 | 0.0698 | 4.0 | 0.0 |
| q10 | hazard | malformed-file honesty, warned | shell | sonnet-5 | readb-nudged | 3 | 100% | 8,798 | 0.0497 | 2.0 | 0.0 |
| q10 | hazard | malformed-file honesty, warned | shell | sonnet-5 | readb-skill | 3 | 100% | 8,769 | 0.0496 | 2.0 | 0.0 |
| q10 | hazard | malformed-file honesty, warned | shell | sonnet-5 | shell-coached | 3 | 100% | 13,468 | 0.0788 | 3.0 | 0.0 |
| q10b | hazard | malformed count, tabular phrasing | shell | haiku-4-5 | baseline | 3 | 100% | 9,435 | 0.0418 | 8.0 | 0.0 |
| q10b | hazard | malformed count, tabular phrasing | shell | haiku-4-5 | readb-bare | 3 | 100% | 9,915 | 0.0330 | 4.0 | 2.0 |
| q10b | hazard | malformed count, tabular phrasing | shell | haiku-4-5 | readb-nudged | 3 | 100% | 11,234 | 0.0433 | 5.0 | 2.0 |
| q10b | hazard | malformed count, tabular phrasing | shell | haiku-4-5 | shell-coached | 3 | 100% | 9,833 | 0.0393 | 6.0 | 0.0 |
| q10b | hazard | malformed count, tabular phrasing | shell | sonnet-5 | baseline | 3 | 100% | 18,019 | 0.1430 | 8.0 | 0.0 |
| q10b | hazard | malformed count, tabular phrasing | shell | sonnet-5 | readb-bare | 3 | 100% | 12,034 | 0.0788 | 4.0 | 2.0 |
| q10b | hazard | malformed count, tabular phrasing | shell | sonnet-5 | readb-nudged | 3 | 100% | 11,277 | 0.0726 | 4.0 | 2.0 |
| q10b | hazard | malformed count, tabular phrasing | shell | sonnet-5 | readb-skill | 3 | 100% | 15,121 | 0.0967 | 6.0 | 2.0 |
| q10b | hazard | malformed count, tabular phrasing | shell | sonnet-5 | shell-coached | 3 | 100% | 13,676 | 0.1060 | 5.0 | 0.0 |
| q11 | retrieval | fuzzy retrieval | read | haiku-4-5 | baseline | 3 | 100% | 12,713 | 0.0480 | 7.0 | 0.0 |
| q11 | retrieval | fuzzy retrieval | read | haiku-4-5 | readb-bare | 3 | 100% | 11,410 | 0.0495 | 8.0 | 0.0 |
| q11 | retrieval | fuzzy retrieval | read | haiku-4-5 | readb-nudged | 3 | 100% | 16,406 | 0.0614 | 11.0 | 3.0 |
| q11 | retrieval | fuzzy retrieval | read | haiku-4-5 | shell-coached | 3 | 100% | 11,949 | 0.0484 | 7.0 | 0.0 |
| q11 | retrieval | fuzzy retrieval | read | sonnet-5 | baseline | 3 | 100% | 16,971 | 0.0966 | 4.0 | 0.0 |
| q11 | retrieval | fuzzy retrieval | read | sonnet-5 | readb-bare | 3 | 100% | 12,077 | 0.0678 | 3.0 | 0.0 |
| q11 | retrieval | fuzzy retrieval | read | sonnet-5 | readb-nudged | 3 | 100% | 12,135 | 0.0682 | 3.0 | 0.0 |
| q11 | retrieval | fuzzy retrieval | read | sonnet-5 | readb-skill | 3 | 100% | 12,397 | 0.0764 | 4.0 | 0.0 |
| q11 | retrieval | fuzzy retrieval | read | sonnet-5 | shell-coached | 3 | 100% | 12,365 | 0.0692 | 3.0 | 0.0 |
| q12 | join | five-part session | readb | haiku-4-5 | baseline | 3 | 67% | 13,355 | 0.0807 | 17.0 | 0.0 |
| q12 | join | five-part session | readb | haiku-4-5 | readb-bare | 3 | 100% | 8,522 | 0.0291 | 7.0 | 6.0 |
| q12 | join | five-part session | readb | haiku-4-5 | readb-nudged | 3 | 100% | 8,471 | 0.0281 | 7.0 | 6.0 |
| q12 | join | five-part session | readb | haiku-4-5 | shell-coached | 3 | 100% | 8,044 | 0.0262 | 3.0 | 0.0 |
| q12 | join | five-part session | readb | sonnet-5 | baseline | 3 | 67% | 11,684 | 0.1048 | 7.0 | 0.0 |
| q12 | join | five-part session | readb | sonnet-5 | readb-bare | 3 | 100% | 10,093 | 0.0601 | 3.0 | 6.0 |
| q12 | join | five-part session | readb | sonnet-5 | readb-nudged | 3 | 100% | 10,160 | 0.0604 | 3.0 | 6.0 |
| q12 | join | five-part session | readb | sonnet-5 | readb-skill | 3 | 100% | 12,726 | 0.0881 | 6.0 | 3.0 |
| q12 | join | five-part session | readb | sonnet-5 | shell-coached | 3 | 100% | 10,199 | 0.0745 | 4.0 | 0.0 |
| q14 | join | body + frontmatter hybrid | readb | haiku-4-5 | baseline | 3 | 100% | 10,928 | 0.0577 | 10.0 | 0.0 |
| q14 | join | body + frontmatter hybrid | readb | haiku-4-5 | readb-bare | 3 | 100% | 27,424 | 0.0833 | 6.0 | 2.0 |
| q14 | join | body + frontmatter hybrid | readb | haiku-4-5 | readb-nudged | 3 | 100% | 25,605 | 0.0663 | 4.0 | 2.0 |
| q14 | join | body + frontmatter hybrid | readb | haiku-4-5 | shell-coached | 3 | 100% | 7,734 | 0.0260 | 3.0 | 0.0 |
| q14 | join | body + frontmatter hybrid | readb | sonnet-5 | baseline | 3 | 100% | 10,654 | 0.0723 | 4.0 | 0.0 |
| q14 | join | body + frontmatter hybrid | readb | sonnet-5 | readb-bare | 3 | 67% | 11,546 | 0.0904 | 6.0 | 4.0 |
| q14 | join | body + frontmatter hybrid | readb | sonnet-5 | readb-nudged | 3 | 100% | 10,823 | 0.0858 | 6.0 | 4.0 |
| q14 | join | body + frontmatter hybrid | readb | sonnet-5 | readb-skill | 3 | 100% | 10,661 | 0.0783 | 5.0 | 0.0 |
| q14 | join | body + frontmatter hybrid | readb | sonnet-5 | shell-coached | 3 | 100% | 9,571 | 0.0514 | 2.0 | 0.0 |
| q15 | scan | output-heavy enumeration | readb | haiku-4-5 | baseline | 3 | 100% | 10,111 | 0.0413 | 6.0 | 0.0 |
| q15 | scan | output-heavy enumeration | readb | haiku-4-5 | readb-bare | 3 | 100% | 8,501 | 0.0318 | 3.0 | 2.0 |
| q15 | scan | output-heavy enumeration | readb | haiku-4-5 | readb-nudged | 3 | 100% | 8,496 | 0.0321 | 3.0 | 2.0 |
| q15 | scan | output-heavy enumeration | readb | haiku-4-5 | shell-coached | 3 | 100% | 9,192 | 0.0308 | 3.0 | 0.0 |
| q15 | scan | output-heavy enumeration | readb | sonnet-5 | baseline | 3 | 100% | 16,847 | 0.1360 | 7.0 | 0.0 |
| q15 | scan | output-heavy enumeration | readb | sonnet-5 | readb-bare | 3 | 100% | 10,830 | 0.0702 | 3.0 | 3.0 |
| q15 | scan | output-heavy enumeration | readb | sonnet-5 | readb-nudged | 3 | 100% | 10,923 | 0.0707 | 3.0 | 3.0 |
| q15 | scan | output-heavy enumeration | readb | sonnet-5 | readb-skill | 3 | 100% | 12,630 | 0.0782 | 4.0 | 1.0 |
| q15 | scan | output-heavy enumeration | readb | sonnet-5 | shell-coached | 3 | 100% | 10,637 | 0.0785 | 4.0 | 0.0 |
| q16 | join | zero result | readb | haiku-4-5 | baseline | 3 | 100% | 14,985 | 0.0865 | 15.0 | 0.0 |
| q16 | join | zero result | readb | haiku-4-5 | readb-bare | 3 | 100% | 8,515 | 0.0310 | 4.0 | 3.0 |
| q16 | join | zero result | readb | haiku-4-5 | readb-nudged | 3 | 100% | 8,284 | 0.0292 | 4.0 | 3.0 |
| q16 | join | zero result | readb | haiku-4-5 | shell-coached | 3 | 100% | 12,215 | 0.0503 | 8.0 | 0.0 |
| q16 | join | zero result | readb | sonnet-5 | baseline | 3 | 100% | 13,807 | 0.1293 | 7.0 | 0.0 |
| q16 | join | zero result | readb | sonnet-5 | readb-bare | 3 | 100% | 9,837 | 0.0575 | 3.0 | 2.0 |
| q16 | join | zero result | readb | sonnet-5 | readb-nudged | 3 | 100% | 10,140 | 0.0729 | 5.0 | 6.0 |
| q16 | join | zero result | readb | sonnet-5 | readb-skill | 3 | 100% | 13,486 | 0.0988 | 7.0 | 6.0 |
| q16 | join | zero result | readb | sonnet-5 | shell-coached | 3 | 100% | 11,964 | 0.1024 | 7.0 | 0.0 |
| q17 | scan | false presupposition | readb | haiku-4-5 | baseline | 3 | 100% | 16,086 | 0.1040 | 21.0 | 0.0 |
| q17 | scan | false presupposition | readb | haiku-4-5 | readb-bare | 3 | 100% | 15,211 | 0.0721 | 12.0 | 3.0 |
| q17 | scan | false presupposition | readb | haiku-4-5 | readb-nudged | 3 | 100% | 19,131 | 0.0855 | 13.0 | 3.0 |
| q17 | scan | false presupposition | readb | haiku-4-5 | shell-coached | 3 | 100% | 11,983 | 0.0766 | 16.0 | 0.0 |
| q17 | scan | false presupposition | readb | sonnet-5 | baseline | 3 | 100% | 19,380 | 0.2718 | 22.0 | 0.0 |
| q17 | scan | false presupposition | readb | sonnet-5 | readb-bare | 3 | 100% | 16,059 | 0.1925 | 15.0 | 4.0 |
| q17 | scan | false presupposition | readb | sonnet-5 | readb-nudged | 3 | 100% | 13,705 | 0.1215 | 9.0 | 4.0 |
| q17 | scan | false presupposition | readb | sonnet-5 | readb-skill | 3 | 100% | 20,694 | 0.2141 | 16.0 | 7.0 |
| q17 | scan | false presupposition | readb | sonnet-5 | shell-coached | 3 | 100% | 13,907 | 0.1150 | 8.0 | 0.0 |
| q18 | hazard | malformed-file honesty, un-warned | shell | haiku-4-5 | baseline | 3 | 33% | 10,420 | 0.0533 | 10.0 | 0.0 |
| q18 | hazard | malformed-file honesty, un-warned | shell | haiku-4-5 | readb-bare | 3 | 0% | 11,245 | 0.0404 | 6.0 | 2.0 |
| q18 | hazard | malformed-file honesty, un-warned | shell | haiku-4-5 | readb-nudged | 3 | 0% | 9,717 | 0.0278 | 3.0 | 2.0 |
| q18 | hazard | malformed-file honesty, un-warned | shell | haiku-4-5 | shell-coached | 3 | 0% | 8,244 | 0.0263 | 3.0 | 0.0 |
| q18 | hazard | malformed-file honesty, un-warned | shell | sonnet-5 | baseline | 3 | 67% | 12,336 | 0.1266 | 7.0 | 0.0 |
| q18 | hazard | malformed-file honesty, un-warned | shell | sonnet-5 | readb-bare | 3 | 100% | 13,710 | 0.0875 | 5.0 | 2.0 |
| q18 | hazard | malformed-file honesty, un-warned | shell | sonnet-5 | readb-nudged | 3 | 100% | 13,501 | 0.0924 | 5.0 | 2.0 |
| q18 | hazard | malformed-file honesty, un-warned | shell | sonnet-5 | readb-skill | 3 | 100% | 13,805 | 0.0869 | 5.0 | 1.0 |
| q18 | hazard | malformed-file honesty, un-warned | shell | sonnet-5 | shell-coached | 3 | 100% | 10,583 | 0.0788 | 5.0 | 0.0 |
| q2 | scan | group-by | readb | haiku-4-5 | baseline | 3 | 67% | 9,338 | 0.0435 | 6.0 | 0.0 |
| q2 | scan | group-by | readb | haiku-4-5 | readb-bare | 3 | 100% | 7,730 | 0.0241 | 3.0 | 2.0 |
| q2 | scan | group-by | readb | haiku-4-5 | readb-nudged | 3 | 100% | 7,747 | 0.0239 | 3.0 | 2.0 |
| q2 | scan | group-by | readb | haiku-4-5 | shell-coached | 3 | 100% | 7,145 | 0.0202 | 2.0 | 0.0 |
| q2 | scan | group-by | readb | sonnet-5 | baseline | 3 | 100% | 17,142 | 0.0899 | 3.0 | 0.0 |
| q2 | scan | group-by | readb | sonnet-5 | readb-bare | 3 | 100% | 10,030 | 0.0650 | 4.0 | 3.0 |
| q2 | scan | group-by | readb | sonnet-5 | readb-nudged | 3 | 100% | 10,143 | 0.0658 | 4.0 | 3.0 |
| q2 | scan | group-by | readb | sonnet-5 | readb-skill | 3 | 100% | 16,407 | 0.0883 | 4.0 | 0.0 |
| q2 | scan | group-by | readb | sonnet-5 | shell-coached | 3 | 100% | 8,915 | 0.0544 | 3.0 | 0.0 |
| q3 | join | filtered listing | readb | haiku-4-5 | baseline | 3 | 67% | 12,724 | 0.0694 | 11.0 | 0.0 |
| q3 | join | filtered listing | readb | haiku-4-5 | readb-bare | 3 | 100% | 7,990 | 0.0260 | 3.0 | 2.0 |
| q3 | join | filtered listing | readb | haiku-4-5 | readb-nudged | 3 | 100% | 8,035 | 0.0262 | 3.0 | 2.0 |
| q3 | join | filtered listing | readb | haiku-4-5 | shell-coached | 3 | 100% | 8,379 | 0.0323 | 4.0 | 0.0 |
| q3 | join | filtered listing | readb | sonnet-5 | baseline | 3 | 67% | 17,188 | 0.1318 | 7.0 | 0.0 |
| q3 | join | filtered listing | readb | sonnet-5 | readb-bare | 3 | 100% | 10,179 | 0.0610 | 3.0 | 3.0 |
| q3 | join | filtered listing | readb | sonnet-5 | readb-nudged | 3 | 100% | 9,139 | 0.0563 | 3.0 | 2.0 |
| q3 | join | filtered listing | readb | sonnet-5 | readb-skill | 3 | 100% | 12,836 | 0.0896 | 6.0 | 3.0 |
| q3 | join | filtered listing | readb | sonnet-5 | shell-coached | 3 | 100% | 14,605 | 0.0930 | 4.0 | 0.0 |
| q4 | join | cross-reference | readb | haiku-4-5 | baseline | 3 | 67% | 14,567 | 0.0700 | 12.0 | 0.0 |
| q4 | join | cross-reference | readb | haiku-4-5 | readb-bare | 3 | 100% | 8,067 | 0.0266 | 3.0 | 2.0 |
| q4 | join | cross-reference | readb | haiku-4-5 | readb-nudged | 3 | 100% | 8,184 | 0.0270 | 3.0 | 2.0 |
| q4 | join | cross-reference | readb | haiku-4-5 | shell-coached | 3 | 100% | 9,320 | 0.0395 | 5.0 | 0.0 |
| q4 | join | cross-reference | readb | sonnet-5 | baseline | 3 | 67% | 14,897 | 0.1238 | 8.0 | 0.0 |
| q4 | join | cross-reference | readb | sonnet-5 | readb-bare | 3 | 100% | 10,389 | 0.0701 | 4.0 | 4.0 |
| q4 | join | cross-reference | readb | sonnet-5 | readb-nudged | 3 | 100% | 10,119 | 0.0603 | 3.0 | 2.0 |
| q4 | join | cross-reference | readb | sonnet-5 | readb-skill | 3 | 100% | 12,004 | 0.0785 | 5.0 | 1.0 |
| q4 | join | cross-reference | readb | sonnet-5 | shell-coached | 3 | 100% | 15,733 | 0.1040 | 4.0 | 0.0 |
| q5 | join | list membership | readb | haiku-4-5 | baseline | 3 | 100% | 10,838 | 0.0441 | 7.0 | 0.0 |
| q5 | join | list membership | readb | haiku-4-5 | readb-bare | 3 | 100% | 7,914 | 0.0252 | 3.0 | 2.0 |
| q5 | join | list membership | readb | haiku-4-5 | readb-nudged | 3 | 100% | 7,917 | 0.0249 | 3.0 | 2.0 |
| q5 | join | list membership | readb | haiku-4-5 | shell-coached | 3 | 100% | 7,552 | 0.0228 | 2.0 | 0.0 |
| q5 | join | list membership | readb | sonnet-5 | baseline | 3 | 100% | 9,896 | 0.0674 | 4.0 | 0.0 |
| q5 | join | list membership | readb | sonnet-5 | readb-bare | 3 | 100% | 9,628 | 0.0640 | 4.0 | 3.0 |
| q5 | join | list membership | readb | sonnet-5 | readb-nudged | 3 | 100% | 9,695 | 0.0644 | 4.0 | 3.0 |
| q5 | join | list membership | readb | sonnet-5 | readb-skill | 3 | 67% | 10,418 | 0.0700 | 4.0 | 0.0 |
| q5 | join | list membership | readb | sonnet-5 | shell-coached | 3 | 100% | 8,878 | 0.0476 | 2.0 | 0.0 |
| q6 | join | extremum | readb | haiku-4-5 | baseline | 3 | 100% | 9,308 | 0.0445 | 8.0 | 0.0 |
| q6 | join | extremum | readb | haiku-4-5 | readb-bare | 3 | 100% | 8,017 | 0.0280 | 4.0 | 2.0 |
| q6 | join | extremum | readb | haiku-4-5 | readb-nudged | 3 | 100% | 7,689 | 0.0233 | 3.0 | 2.0 |
| q6 | join | extremum | readb | haiku-4-5 | shell-coached | 3 | 100% | 7,303 | 0.0212 | 2.0 | 0.0 |
| q6 | join | extremum | readb | sonnet-5 | baseline | 3 | 100% | 10,095 | 0.0828 | 6.0 | 0.0 |
| q6 | join | extremum | readb | sonnet-5 | readb-bare | 3 | 100% | 9,814 | 0.0658 | 4.0 | 3.0 |
| q6 | join | extremum | readb | sonnet-5 | readb-nudged | 3 | 100% | 9,889 | 0.0581 | 3.0 | 2.0 |
| q6 | join | extremum | readb | sonnet-5 | readb-skill | 3 | 100% | 12,876 | 0.0868 | 6.0 | 3.0 |
| q6 | join | extremum | readb | sonnet-5 | shell-coached | 3 | 100% | 8,766 | 0.0467 | 2.0 | 0.0 |
| q7 | retrieval | exact-phrase needle | shell | haiku-4-5 | baseline | 3 | 100% | 6,800 | 0.0192 | 2.0 | 0.0 |
| q7 | retrieval | exact-phrase needle | shell | haiku-4-5 | readb-bare | 3 | 100% | 6,851 | 0.0190 | 2.0 | 0.0 |
| q7 | retrieval | exact-phrase needle | shell | haiku-4-5 | readb-nudged | 3 | 100% | 7,734 | 0.0238 | 3.0 | 2.0 |
| q7 | retrieval | exact-phrase needle | shell | haiku-4-5 | shell-coached | 3 | 100% | 7,043 | 0.0192 | 2.0 | 0.0 |
| q7 | retrieval | exact-phrase needle | shell | sonnet-5 | baseline | 3 | 100% | 8,356 | 0.0446 | 2.0 | 0.0 |
| q7 | retrieval | exact-phrase needle | shell | sonnet-5 | readb-bare | 3 | 100% | 8,489 | 0.0454 | 2.0 | 0.0 |
| q7 | retrieval | exact-phrase needle | shell | sonnet-5 | readb-nudged | 3 | 100% | 8,557 | 0.0457 | 2.0 | 0.0 |
| q7 | retrieval | exact-phrase needle | shell | sonnet-5 | readb-skill | 3 | 100% | 8,469 | 0.0451 | 2.0 | 0.0 |
| q7 | retrieval | exact-phrase needle | shell | sonnet-5 | shell-coached | 3 | 100% | 8,726 | 0.0461 | 2.0 | 0.0 |
| q8 | join | multi-hop | readb | haiku-4-5 | baseline | 3 | 33% | 18,026 | 0.1043 | 13.0 | 0.0 |
| q8 | join | multi-hop | readb | haiku-4-5 | readb-bare | 3 | 100% | 10,260 | 0.0352 | 4.0 | 3.0 |
| q8 | join | multi-hop | readb | haiku-4-5 | readb-nudged | 3 | 100% | 8,413 | 0.0285 | 3.0 | 2.0 |
| q8 | join | multi-hop | readb | haiku-4-5 | shell-coached | 3 | 100% | 13,232 | 0.0645 | 9.0 | 0.0 |
| q8 | join | multi-hop | readb | sonnet-5 | baseline | 3 | 67% | 16,581 | 0.1421 | 8.0 | 0.0 |
| q8 | join | multi-hop | readb | sonnet-5 | readb-bare | 3 | 100% | 12,914 | 0.0889 | 4.0 | 5.0 |
| q8 | join | multi-hop | readb | sonnet-5 | readb-nudged | 3 | 100% | 10,253 | 0.0620 | 3.0 | 2.0 |
| q8 | join | multi-hop | readb | sonnet-5 | readb-skill | 3 | 100% | 13,324 | 0.0841 | 5.0 | 2.0 |
| q8 | join | multi-hop | readb | sonnet-5 | shell-coached | 3 | 100% | 14,362 | 0.1341 | 6.0 | 0.0 |
| q9 | retrieval | single-file lookup | read | haiku-4-5 | baseline | 3 | 100% | 7,697 | 0.0238 | 3.0 | 0.0 |
| q9 | retrieval | single-file lookup | read | haiku-4-5 | readb-bare | 3 | 100% | 7,561 | 0.0234 | 3.0 | 0.0 |
| q9 | retrieval | single-file lookup | read | haiku-4-5 | readb-nudged | 3 | 100% | 7,788 | 0.0241 | 3.0 | 2.0 |
| q9 | retrieval | single-file lookup | read | haiku-4-5 | shell-coached | 3 | 100% | 7,075 | 0.0196 | 2.0 | 0.0 |
| q9 | retrieval | single-file lookup | read | sonnet-5 | baseline | 3 | 100% | 8,830 | 0.0540 | 3.0 | 0.0 |
| q9 | retrieval | single-file lookup | read | sonnet-5 | readb-bare | 3 | 100% | 9,079 | 0.0620 | 4.0 | 2.0 |
| q9 | retrieval | single-file lookup | read | sonnet-5 | readb-nudged | 3 | 100% | 9,158 | 0.0628 | 4.0 | 2.0 |
| q9 | retrieval | single-file lookup | read | sonnet-5 | readb-skill | 3 | 100% | 8,924 | 0.0543 | 3.0 | 0.0 |
| q9 | retrieval | single-file lookup | read | sonnet-5 | shell-coached | 3 | 100% | 8,721 | 0.0465 | 2.0 | 0.0 |

## Overhead-subtracted cost ratios — a choice, not a correction

The floor is a trivial prompt through the identical harness, so it measures the **runtime's** fixed cost under each arm's configuration — not that arm's own preamble, which is its treatment and is deliberately never subtracted. A ratio below 1.00 always moves further from 1.00 when a constant is removed from both sides, so which constant is removed is a choice; both rules are shown, neither as the authoritative one.

| model | arm | one floor per run | one prompt prefix per turn |
|---|---|---|---|
| haiku-4-5 | readb-bare | 0.65x | 0.46x |
| haiku-4-5 | readb-nudged | 0.39x | 0.24x |
| haiku-4-5 | shell-coached | 0.55x | 0.30x |
| sonnet-5 | readb-bare | 0.59x | 0.44x |
| sonnet-5 | readb-nudged | 0.50x | 0.32x |
| sonnet-5 | readb-skill | 0.78x | 0.93x |
| sonnet-5 | shell-coached | 0.61x | 0.46x |

## Integrity

| model | arm | runs | no tool call | skill fired | compacted | denials | readb never used |
|---|---|---|---|---|---|---|---|
| haiku-4-5 | baseline | 78 | 0 | 0 | 0 | 0 | 0 |
| haiku-4-5 | readb-bare | 78 | 0 | 0 | 0 | 0 | 16 |
| haiku-4-5 | readb-nudged | 78 | 0 | 0 | 0 | 0 | 7 |
| haiku-4-5 | shell-coached | 78 | 0 | 0 | 0 | 0 | 0 |
| sonnet-5 | baseline | 78 | 0 | 0 | 0 | 0 | 0 |
| sonnet-5 | readb-bare | 78 | 0 | 0 | 0 | 0 | 13 |
| sonnet-5 | readb-nudged | 78 | 0 | 0 | 0 | 0 | 10 |
| sonnet-5 | readb-skill | 78 | 0 | 37 | 0 | 0 | 41 |
| sonnet-5 | shell-coached | 78 | 0 | 0 | 0 | 0 | 0 |

## Appendix — the demoted metrics

| model | arm | cost, cache-neutral (USD) | wall clock (s) | output tokens |
|---|---|---|---|---|
| haiku-4-5 | baseline | 0.2111 | 23.5 | 1,652 |
| haiku-4-5 | readb-bare | 0.1016 | 16.5 | 1,084 |
| haiku-4-5 | readb-nudged | 0.0759 | 12.7 | 882 |
| haiku-4-5 | shell-coached | 0.0960 | 14.1 | 1,111 |
| sonnet-5 | baseline | 0.3787 | 16.4 | 912 |
| sonnet-5 | readb-bare | 0.2488 | 11.9 | 418 |
| sonnet-5 | readb-nudged | 0.2477 | 9.8 | 388 |
| sonnet-5 | readb-skill | 0.2700 | 11.7 | 590 |
| sonnet-5 | shell-coached | 0.2141 | 11.8 | 638 |

## Every wrong answer

- b1 haiku-4-5 baseline r2: answered `['041-document-the-duplicate-detector', '070-fix-the-media-server-handshake', '083-extend-the-duplicate-detector', '204-simplify-the-media-server-handshake', '259-rework-the-storage-migration', '312-harden-the-search-index']` (partial 0.75, tool shell)
- b1 haiku-4-5 baseline r3: answered `['070-fix-the-media-server-handshake', '083-extend-the-duplicate-detector', '204-simplify-the-media-server-handshake', '259-rework-the-storage-migration', '312-harden-the-search-index']` (partial 0.6667, tool shell)
- b3 haiku-4-5 baseline r1: answered `[]` (partial 0.0, tool shell)
- b4 haiku-4-5 readb-bare r1: answered `['016-extend-the-search-index', '020-add-exif-extraction', '038-rework-the-search-index', '063-simplify-the-media-server-handshake', '144-extend-the-duplicate-detector', '246-simplify-the-duplicate-detector', '251-rework-the-search-index', '376-simplify-the-search-index']` (partial 0.8889, tool shell)
- b6 haiku-4-5 baseline r3: answered `{}` (partial 0.0, tool shell)
- b6 haiku-4-5 shell-coached r2: answered `{'033-extend-the-thumbnail-cache': 'too-costly', '207-simplify-the-storage-migration': 'too-costly', '321-document-album-sharing-links': 'out-of-scope', '357-document-backup-verification': 'obsolete'}` (partial 0.6667, tool shell)
- b6 sonnet-5 baseline r1: answered `{'357-document-backup-verification': 'obsolete', '033-extend-the-thumbnail-cache': 'too-costly', '321-document-album-sharing-links': 'out-of-scope', '207-simplify-the-storage-migration': 'too-costly'}` (partial 0.6667, tool shell)
- b6 sonnet-5 baseline r2: answered `{'207-simplify-the-storage-migration': 'too-costly', '357-document-backup-verification': 'obsolete', '033-extend-the-thumbnail-cache': 'too-costly'}` (partial 0.5, tool shell)
- b6 sonnet-5 baseline r3: answered `{'207-simplify-the-storage-migration': 'too-costly', '033-extend-the-thumbnail-cache': 'too-costly', '321-document-album-sharing-links': 'out-of-scope', '357-document-backup-verification': 'obsolete'}` (partial 0.6667, tool shell)
- b6 sonnet-5 readb-skill r1: answered `{'207-simplify-the-storage-migration': 'too-costly', '033-extend-the-thumbnail-cache': 'too-costly', '321-document-album-sharing-links': 'out-of-scope', '357-document-backup-verification': 'obsolete'}` (partial 0.6667, tool shell)
- b6 sonnet-5 readb-skill r3: answered `{'033-extend-the-thumbnail-cache': 'too-costly', '207-simplify-the-storage-migration': 'too-costly', '321-document-album-sharing-links': 'out-of-scope', '357-document-backup-verification': 'obsolete'}` (partial 0.6667, tool shell)
- b7 haiku-4-5 baseline r1: answered `379` (partial 0.0, tool shell)
- b7 haiku-4-5 baseline r2: answered `379` (partial 0.0, tool shell)
- b7 haiku-4-5 baseline r3: answered `379` (partial 0.0, tool shell)
- b7 haiku-4-5 readb-bare r1: answered `379` (partial 0.0, tool shell)
- b7 haiku-4-5 readb-bare r3: answered `379` (partial 0.0, tool shell)
- b7 haiku-4-5 readb-nudged r1: answered `379` (partial 0.0, tool shell)
- b7 haiku-4-5 readb-nudged r2: answered `379` (partial 0.0, tool shell)
- b7 haiku-4-5 shell-coached r2: answered `379` (partial 0.0, tool shell)
- b7 sonnet-5 baseline r1: answered `379` (partial 0.0, tool shell)
- b7 sonnet-5 baseline r2: answered `379` (partial 0.0, tool shell)
- b7 sonnet-5 readb-bare r3: answered `379` (partial 0.0, tool readb)
- b8 haiku-4-5 baseline r1: answered `{'search': 9, 'performance': 8, 'metadata': 7, 'packaging': 7, 'storage': 7, 'sync': 6, 'api': 5, 'ingest': 5, 'thumbnails': 5, 'ui': 4}` (partial 0.0, tool shell)
- b8 haiku-4-5 baseline r2: answered `{'search': 20, 'performance': 19, 'storage': 18, 'metadata': 17, 'ui': 15, 'sync': 15, 'packaging': 14, 'api': 14, 'ingest': 13, 'thumbnails': 11}` (partial 0.0, tool shell)
- b8 haiku-4-5 baseline r3: answered `{'api': 5, 'ingest': 5, 'metadata': 7, 'packaging': 7, 'performance': 8, 'search': 9, 'storage': 7, 'sync': 6, 'thumbnails': 5, 'ui': 4}` (partial 0.0, tool shell)
- b8 haiku-4-5 shell-coached r1: answered `{'search': 20, 'performance': 19, 'storage': 18, 'metadata': 17, 'ui': 15, 'sync': 15, 'packaging': 14, 'api': 14, 'ingest': 13, 'thumbnails': 11}` (partial 0.0, tool shell)
- b8 sonnet-5 baseline r3: answered `{'search': 20, 'performance': 19, 'storage': 18, 'metadata': 17, 'ui': 15, 'sync': 15, 'packaging': 14, 'api': 14, 'ingest': 13, 'thumbnails': 11}` (partial 0.0, tool shell)
- b8 sonnet-5 shell-coached r1: answered `{'search': 20, 'performance': 19, 'storage': 18, 'metadata': 17, 'ui': 15, 'sync': 15, 'packaging': 14, 'api': 14, 'ingest': 13, 'thumbnails': 11}` (partial 0.0, tool shell)
- b8 sonnet-5 shell-coached r3: answered `{'search': 20, 'performance': 19, 'storage': 18, 'metadata': 17, 'ui': 15, 'sync': 15, 'packaging': 14, 'api': 14, 'ingest': 13, 'thumbnails': 11}` (partial 0.0, tool shell)
- q1 sonnet-5 baseline r1: answered `{'runbook': 396, 'service': 360, 'incident': 324, 'decision': 120}` (partial 0.0, tool shell)
- q12 haiku-4-5 baseline r2: answered `{'a': 62, 'b': 38, 'c': 34, 'd': 6, 'e': 5}` (partial 0.0, tool shell)
- q12 sonnet-5 baseline r3: answered `{'a': 65, 'b': 56, 'c': 45, 'd': 18, 'e': 25}` (partial 0.2, tool shell)
- q14 sonnet-5 readb-bare r3: answered `['inc-0007', 'inc-0063', 'inc-0081', 'inc-0083', 'inc-0084', 'inc-0101', 'inc-0113', 'inc-0125', 'inc-0155']` (partial 0.8182, tool shell)
- q18 haiku-4-5 baseline r2: answered `{'team': 'platform', 'count': '31'}` (partial 0.0, tool shell)
- q18 haiku-4-5 baseline r3: answered `{'team': 'platform', 'count': '31'}` (partial 0.0, tool shell)
- q18 haiku-4-5 readb-bare r1: answered `{'team': 'platform', 'count': '31'}` (partial 0.0, tool readb)
- q18 haiku-4-5 readb-bare r2: answered `{'team': 'platform', 'count': '31'}` (partial 0.0, tool readb)
- q18 haiku-4-5 readb-bare r3: answered `{'team': 'platform', 'count': '31'}` (partial 0.0, tool readb)
- q18 haiku-4-5 readb-nudged r1: answered `{'team': 'platform', 'count': '31'}` (partial 0.0, tool readb)
- q18 haiku-4-5 readb-nudged r2: answered `{'team': 'platform', 'count': '31'}` (partial 0.0, tool readb)
- q18 haiku-4-5 readb-nudged r3: answered `{'team': 'platform', 'count': '31'}` (partial 0.0, tool readb)
- q18 haiku-4-5 shell-coached r1: answered `{'team': 'platform', 'count': '31'}` (partial 0.0, tool shell)
- q18 haiku-4-5 shell-coached r2: answered `{'team': 'platform', 'count': '31'}` (partial 0.0, tool shell)
- q18 haiku-4-5 shell-coached r3: answered `{'team': 'platform', 'count': '31'}` (partial 0.0, tool shell)
- q18 sonnet-5 baseline r2: answered `{'team': 'platform', 'count': '31'}` (partial 0.0, tool shell)
- q2 haiku-4-5 baseline r1: answered `{'beta': 49, 'deprecated': 49, 'ga': 39, 'incubating': 43, 'none': 180}` (partial 1.0, tool shell)
- q3 haiku-4-5 baseline r1: answered `['svc-0042-core-validator', 'svc-0045-batch-router', 'svc-0046-unified-ledger', 'svc-0047-shadow-scheduler', 'svc-0064-edge-gateway', 'svc-0070-regional-aggregator', 'svc-0072-inline-cache', 'svc-0080-unified-aggregator', 'svc-0113-unified-planner', 'svc-0139-legacy-indexer', 'svc-0179-core-validator']` (partial 0.9565, tool shell)
- q3 sonnet-5 baseline r2: answered `['svc-0042-core-validator', 'svc-0045-batch-router', 'svc-0046-unified-ledger', 'svc-0047-shadow-scheduler', 'svc-0064-edge-gateway', 'svc-0070-regional-aggregator', 'svc-0072-inline-cache', 'svc-0080-unified-aggregator', 'svc-0113-unified-planner', 'svc-0139-legacy-indexer', 'svc-0179-core-validator']` (partial 0.9565, tool shell)
- q4 haiku-4-5 baseline r2: answered `['rb-0024-shadow-aggregator', 'rb-0026-legacy-gateway', 'rb-0090-legacy-gateway', 'rb-0142-async-router', 'rb-0158-inline-validator', 'rb-0179-core-validator', 'rb-0182-unified-cache']` (partial 0.7368, tool shell)
- q4 sonnet-5 baseline r2: answered `['rb-0024-shadow-aggregator', 'rb-0026-legacy-gateway', 'rb-0090-legacy-gateway', 'rb-0092-stream-reconciler', 'rb-0141-legacy-gateway', 'rb-0142-async-router', 'rb-0158-inline-validator', 'rb-0179-core-validator', 'rb-0180-core-validator', 'rb-0182-unified-cache']` (partial 0.9091, tool shell)
- q5 sonnet-5 readb-skill r1: answered `['inc-0027', 'inc-0084', 'inc-0140']` (partial 0.6, tool shell)
- q8 haiku-4-5 baseline r1: answered `['rb-0045-batch-scheduler', 'rb-0050-core-ledger', 'rb-0151-legacy-cache', 'rb-0168-async-notifier', 'rb-0184-batch-reconciler']` (partial 0.625, tool shell)
- q8 haiku-4-5 baseline r2: answered `['rb-0005-batch-scheduler', 'rb-0045-batch-scheduler', 'rb-0117-batch-reconciler', 'rb-0184-batch-reconciler']` (partial 0.5333, tool shell)
- q8 sonnet-5 baseline r1: answered `['rb-0005-batch-scheduler', 'rb-0045-batch-scheduler', 'rb-0050-core-ledger', 'rb-0117-batch-reconciler', 'rb-0151-legacy-cache', 'rb-0168-async-notifier', 'rb-0184-batch-reconciler', 'rb-0186-legacy-resolver']` (partial 0.8421, tool shell)

Total reported spend: $46.34
