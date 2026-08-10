# Benchmark results

72 runs recorded, 0 excluded as invalid, 72 used.

## Per arm, all questions pooled

| arm | n | exact | partial credit | cost, as billed (USD) | cost, cache-neutral (USD) | new tokens ingested | wall clock (s) | output tokens | turns | cumulative prompt tokens |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 36 | 97% | 0.97 | 0.1011 | 0.3698 | 9,739 | 11.4 | 453 | 4.0 | 120,302 |
| readb-skill | 36 | 100% | 1.00 | 0.1157 | 0.3913 | 12,041 | 12.0 | 431 | 5.0 | 127,794 |

## Ratio to baseline, paired by question (below 1.00 favours the arm)

| arm | cost, as billed (USD) [95% CI] | cost, cache-neutral (USD) [95% CI] | new tokens ingested [95% CI] | wall clock (s) [95% CI] | output tokens [95% CI] | turns [95% CI] | cumulative prompt tokens [95% CI] |
|---|---|---|---|---|---|---|---|
| readb-skill | 1.01× [0.89–1.18] | 1.00× [0.81–1.06] | 1.04× [0.97–1.28] | 1.03× [0.82–1.16] | 0.70× [0.58–0.94] | 1.00× [0.88–1.29] | 1.00× [0.82–1.07] |

## By question shape

| question | shape | favours | arm | n | exact | ingested | cost (neutral) | wall (s) | turns | readb calls |
|---|---|---|---|---|---|---|---|---|---|---|
| q1 | type rollup | sql | baseline | 3 | 100% | 8,469 | 0.3595 | 11.5 | 4.0 | 0.0 |
| q1 | type rollup | sql | readb-skill | 3 | 100% | 11,545 | 0.3882 | 12.9 | 5.0 | 2.0 |
| q10 | malformed-file honesty | files | baseline | 3 | 100% | 17,349 | 0.5962 | 24.5 | 6.0 | 0.0 |
| q10 | malformed-file honesty | files | readb-skill | 3 | 100% | 15,967 | 0.5355 | 32.6 | 6.0 | 0.0 |
| q11 | fuzzy retrieval | files | baseline | 3 | 100% | 12,014 | 0.3745 | 10.7 | 4.0 | 0.0 |
| q11 | fuzzy retrieval | files | readb-skill | 3 | 100% | 12,127 | 0.3759 | 11.9 | 4.0 | 0.0 |
| q12 | five-part session | neutral | baseline | 3 | 100% | 9,604 | 0.3719 | 14.2 | 4.0 | 0.0 |
| q12 | five-part session | neutral | readb-skill | 3 | 100% | 12,820 | 0.3985 | 12.1 | 5.0 | 2.0 |
| q2 | group-by | sql | baseline | 3 | 100% | 8,757 | 0.2725 | 10.3 | 3.0 | 0.0 |
| q2 | group-by | sql | readb-skill | 3 | 100% | 11,380 | 0.2869 | 9.1 | 4.0 | 1.0 |
| q3 | filtered listing | sql | baseline | 3 | 100% | 10,297 | 0.5618 | 20.1 | 6.0 | 0.0 |
| q3 | filtered listing | sql | readb-skill | 3 | 100% | 12,518 | 0.4953 | 15.9 | 6.0 | 3.0 |
| q4 | cross-reference | sql | baseline | 3 | 100% | 12,071 | 0.9755 | 23.4 | 10.0 | 0.0 |
| q4 | cross-reference | sql | readb-skill | 3 | 100% | 12,072 | 0.3943 | 15.1 | 5.0 | 2.0 |
| q5 | list membership | sql | baseline | 3 | 100% | 10,755 | 0.2804 | 9.2 | 3.0 | 0.0 |
| q5 | list membership | sql | readb-skill | 3 | 100% | 11,470 | 0.2885 | 9.5 | 4.0 | 1.0 |
| q6 | extremum | sql | baseline | 3 | 67% | 9,742 | 0.3686 | 9.9 | 4.0 | 0.0 |
| q6 | extremum | sql | readb-skill | 3 | 100% | 12,357 | 0.4914 | 12.2 | 6.0 | 3.0 |
| q7 | exact-phrase needle | files | baseline | 3 | 100% | 8,078 | 0.1772 | 5.0 | 2.0 | 0.0 |
| q7 | exact-phrase needle | files | readb-skill | 3 | 100% | 8,192 | 0.1778 | 5.1 | 2.0 | 0.0 |
| q8 | multi-hop | sql | baseline | 3 | 100% | 14,026 | 0.8715 | 26.5 | 9.0 | 0.0 |
| q8 | multi-hop | sql | readb-skill | 3 | 100% | 12,872 | 0.3981 | 13.3 | 5.0 | 2.0 |
| q9 | single-file lookup | files | baseline | 3 | 100% | 9,052 | 0.3587 | 7.5 | 4.0 | 0.0 |
| q9 | single-file lookup | files | readb-skill | 3 | 100% | 8,552 | 0.2680 | 8.9 | 3.0 | 0.0 |

## Floor-subtracted cost ratios (one floor per run; see the caveat)

| arm | billed | cache-neutral |
|---|---|---|
| readb-skill | 1.00× | 1.00× |

## Cost ratio to baseline, by the shape a question was declared to favour

| arm | files (n=4) | neutral (n=1) | sql (n=7) |
|---|---|---|---|
| readb-skill | 0.96× | 1.17× | 1.01× |

## Integrity

| arm | runs | unsupported | skill fired | compacted | denials | readb never used |
|---|---|---|---|---|---|---|
| baseline | 36 | 0 | 0 | 0 | 0 | 0 |
| readb-skill | 36 | 0 | 28 | 0 | 0 | 11 |

## Every wrong answer

- q6 baseline r3: answered `{'team-name': 31}` (partial 0.0)

Total reported spend: $8.33
