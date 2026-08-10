# Benchmark results

144 runs recorded, 36 excluded as invalid, 108 used.

## Per arm, all questions pooled

| arm | n | exact | partial credit | cost, as billed (USD) | cost, cache-neutral (USD) | new tokens ingested | wall clock (s) | output tokens | turns | cumulative prompt tokens |
|---|---|---|---|---|---|---|---|---|---|---|
| shell-coached | 36 | 100% | 1.00 | 0.0983 | 0.3678 | 9,051 | 11.8 | 512 | 4.0 | 119,574 |
| baseline | 36 | 97% | 0.97 | 0.1011 | 0.3698 | 9,739 | 11.4 | 453 | 4.0 | 120,302 |
| readb-bare | 36 | 94% | 0.94 | 0.0877 | 0.2780 | 9,542 | 10.6 | 338 | 3.0 | 90,790 |
| readb-skill | 0 | — | — | — | — | — | — | — | — | — | *(all runs excluded — see below)*

## Ratio to baseline, paired by question (below 1.00 favours the arm)

| arm | cost, as billed (USD) [95% CI] | cost, cache-neutral (USD) [95% CI] | new tokens ingested [95% CI] | wall clock (s) [95% CI] | output tokens [95% CI] | turns [95% CI] | cumulative prompt tokens [95% CI] |
|---|---|---|---|---|---|---|---|
| baseline | 1.04× [1.00–1.15] | 1.01× [0.98–1.27] | 1.05× [1.03–1.10] | 1.05× [0.86–1.27] | 1.02× [0.96–1.44] | 1.00× [1.00–1.27] | 1.00× [0.98–1.27] |
| readb-bare | 0.90× [0.79–1.05] | 0.76× [0.60–1.01] | 1.02× [0.99–1.10] | 1.03× [0.70–1.30] | 0.74× [0.41–1.08] | 0.75× [0.60–1.00] | 0.76× [0.61–1.01] |
| readb-skill | — | — | — | — | — | — | — |

## By question shape

| question | shape | favours | arm | n | exact | ingested | cost (neutral) | wall (s) | turns | readb calls |
|---|---|---|---|---|---|---|---|---|---|---|
| q1 | type rollup | sql | shell-coached | 3 | 100% | 8,430 | 0.2697 | 7.9 | 3.0 | 0.0 |
| q1 | type rollup | sql | baseline | 3 | 100% | 8,469 | 0.3595 | 11.5 | 4.0 | 0.0 |
| q1 | type rollup | sql | readb-bare | 3 | 100% | 9,445 | 0.2767 | 16.4 | 3.0 | 2.0 |
| q10 | malformed-file honesty | files | shell-coached | 3 | 100% | 8,592 | 0.2743 | 16.3 | 3.0 | 0.0 |
| q10 | malformed-file honesty | files | baseline | 3 | 100% | 17,349 | 0.5962 | 24.5 | 6.0 | 0.0 |
| q10 | malformed-file honesty | files | readb-bare | 3 | 100% | 10,153 | 0.7416 | 30.4 | 7.0 | 0.0 |
| q11 | fuzzy retrieval | files | shell-coached | 3 | 100% | 11,686 | 0.3707 | 8.3 | 4.0 | 0.0 |
| q11 | fuzzy retrieval | files | baseline | 3 | 100% | 12,014 | 0.3745 | 10.7 | 4.0 | 0.0 |
| q11 | fuzzy retrieval | files | readb-bare | 3 | 100% | 11,801 | 0.2824 | 8.4 | 3.0 | 0.0 |
| q12 | five-part session | neutral | shell-coached | 3 | 100% | 9,260 | 0.3713 | 13.4 | 4.0 | 0.0 |
| q12 | five-part session | neutral | baseline | 3 | 100% | 9,604 | 0.3719 | 14.2 | 4.0 | 0.0 |
| q12 | five-part session | neutral | readb-bare | 3 | 100% | 9,602 | 0.2774 | 14.2 | 3.0 | 6.0 |
| q2 | group-by | sql | shell-coached | 3 | 100% | 8,380 | 0.2691 | 8.2 | 3.0 | 0.0 |
| q2 | group-by | sql | baseline | 3 | 100% | 8,757 | 0.2725 | 10.3 | 3.0 | 0.0 |
| q2 | group-by | sql | readb-bare | 3 | 100% | 9,544 | 0.3647 | 11.9 | 4.0 | 3.0 |
| q3 | filtered listing | sql | shell-coached | 3 | 100% | 9,434 | 0.4642 | 22.6 | 5.0 | 0.0 |
| q3 | filtered listing | sql | baseline | 3 | 100% | 10,297 | 0.5618 | 20.1 | 6.0 | 0.0 |
| q3 | filtered listing | sql | readb-bare | 3 | 100% | 9,540 | 0.2767 | 9.9 | 3.0 | 2.0 |
| q4 | cross-reference | sql | shell-coached | 3 | 100% | 10,429 | 0.6585 | 22.6 | 7.0 | 0.0 |
| q4 | cross-reference | sql | baseline | 3 | 100% | 12,071 | 0.9755 | 23.4 | 10.0 | 0.0 |
| q4 | cross-reference | sql | readb-bare | 3 | 100% | 9,807 | 0.3739 | 14.3 | 4.0 | 4.0 |
| q5 | list membership | sql | shell-coached | 3 | 100% | 9,617 | 0.3675 | 10.7 | 4.0 | 0.0 |
| q5 | list membership | sql | baseline | 3 | 100% | 10,755 | 0.2804 | 9.2 | 3.0 | 0.0 |
| q5 | list membership | sql | readb-bare | 3 | 100% | 9,483 | 0.2760 | 11.6 | 3.0 | 3.0 |
| q6 | extremum | sql | shell-coached | 3 | 100% | 8,966 | 0.4530 | 11.5 | 5.0 | 0.0 |
| q6 | extremum | sql | baseline | 3 | 67% | 9,742 | 0.3686 | 9.9 | 4.0 | 0.0 |
| q6 | extremum | sql | readb-bare | 3 | 33% | 9,294 | 0.2734 | 8.9 | 3.0 | 2.0 |
| q7 | exact-phrase needle | files | shell-coached | 3 | 100% | 8,202 | 0.1779 | 4.6 | 2.0 | 0.0 |
| q7 | exact-phrase needle | files | baseline | 3 | 100% | 8,078 | 0.1772 | 5.0 | 2.0 | 0.0 |
| q7 | exact-phrase needle | files | readb-bare | 3 | 100% | 8,167 | 0.1777 | 5.3 | 2.0 | 0.0 |
| q8 | multi-hop | sql | shell-coached | 3 | 100% | 13,266 | 0.8959 | 32.3 | 9.0 | 0.0 |
| q8 | multi-hop | sql | baseline | 3 | 100% | 14,026 | 0.8715 | 26.5 | 9.0 | 0.0 |
| q8 | multi-hop | sql | readb-bare | 3 | 100% | 9,622 | 0.2786 | 11.3 | 3.0 | 2.0 |
| q9 | single-file lookup | files | shell-coached | 3 | 100% | 8,617 | 0.3584 | 9.9 | 4.0 | 0.0 |
| q9 | single-file lookup | files | baseline | 3 | 100% | 9,052 | 0.3587 | 7.5 | 4.0 | 0.0 |
| q9 | single-file lookup | files | readb-bare | 3 | 100% | 9,276 | 0.3584 | 8.1 | 4.0 | 0.0 |

## Cost ratio to baseline, by the shape a question was declared to favour

| arm | files (n=4) | neutral (n=1) | sql (n=7) |
|---|---|---|---|
| baseline | 1.04× | 1.03× | 1.05× |
| readb-bare | 1.00× | 0.87× | 0.81× |
| readb-skill | — | — | — |

## Integrity

| arm | runs | unsupported | skill fired | compacted | denials | readb never used |
|---|---|---|---|---|---|---|
| shell-coached | 36 | 0 | 0 | 0 | 0 | 0 |
| baseline | 36 | 0 | 0 | 0 | 0 | 36 |
| readb-bare | 36 | 0 | 0 | 0 | 0 | 12 |

## Excluded runs

- readb-skill q1 r1: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q2 r1: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q3 r1: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q4 r1: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q5 r1: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q6 r1: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q7 r1: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q8 r1: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q9 r1: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q10 r1: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q11 r1: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q12 r1: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q2 r2: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q3 r2: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q4 r2: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q5 r2: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q6 r2: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q7 r2: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q8 r2: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q9 r2: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q10 r2: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q11 r2: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q12 r2: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q1 r2: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q3 r3: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q4 r3: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q5 r3: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q6 r3: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q7 r3: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q8 r3: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q9 r3: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q10 r3: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q11 r3: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q12 r3: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q1 r3: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.
- readb-skill q2 r3: environment defect: the shipped skill's leading example is `uvx readb` and this arm had no uv on PATH, so 17 of 36 runs paid an exit-127 recovery. Re-measured in skill_uv.jsonl. Kept as the record of the retraction.

## Every wrong answer

- q6 baseline r3: answered `{'team-name': 31}` (partial 0.0)
- q6 readb-bare r2: answered `{'team-name': 31}` (partial 0.0)
- q6 readb-bare r3: answered `{'count': 31}` (partial 0.0)

Total reported spend: $16.51
