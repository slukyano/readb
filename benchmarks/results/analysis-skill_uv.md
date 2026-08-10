# Benchmark results

36 runs recorded, 0 excluded as invalid, 36 used.

## Per arm, all questions pooled

| arm | n | exact | partial credit | cost, as billed (USD) | cost, cache-neutral (USD) | new tokens ingested | wall clock (s) | output tokens | turns | cumulative prompt tokens |
|---|---|---|---|---|---|---|---|---|---|---|
| readb-skill | 36 | 100% | 1.00 | 0.1157 | 0.3913 | 12,041 | 12.0 | 431 | 5.0 | 127,794 |

## Ratio to baseline, paired by question (below 1.00 favours the arm)

| arm | cost, as billed (USD) [95% CI] | cost, cache-neutral (USD) [95% CI] | new tokens ingested [95% CI] | wall clock (s) [95% CI] | output tokens [95% CI] | turns [95% CI] | cumulative prompt tokens [95% CI] |
|---|---|---|---|---|---|---|---|
| readb-skill | — | — | — | — | — | — | — |

## By question shape

| question | shape | favours | arm | n | exact | ingested | cost (neutral) | wall (s) | turns | readb calls |
|---|---|---|---|---|---|---|---|---|---|---|
| q1 | type rollup | sql | readb-skill | 3 | 100% | 11,545 | 0.3882 | 12.9 | 5.0 | 2.0 |
| q10 | malformed-file honesty | files | readb-skill | 3 | 100% | 15,967 | 0.5355 | 32.6 | 6.0 | 0.0 |
| q11 | fuzzy retrieval | files | readb-skill | 3 | 100% | 12,127 | 0.3759 | 11.9 | 4.0 | 0.0 |
| q12 | five-part session | neutral | readb-skill | 3 | 100% | 12,820 | 0.3985 | 12.1 | 5.0 | 2.0 |
| q2 | group-by | sql | readb-skill | 3 | 100% | 11,380 | 0.2869 | 9.1 | 4.0 | 1.0 |
| q3 | filtered listing | sql | readb-skill | 3 | 100% | 12,518 | 0.4953 | 15.9 | 6.0 | 3.0 |
| q4 | cross-reference | sql | readb-skill | 3 | 100% | 12,072 | 0.3943 | 15.1 | 5.0 | 2.0 |
| q5 | list membership | sql | readb-skill | 3 | 100% | 11,470 | 0.2885 | 9.5 | 4.0 | 1.0 |
| q6 | extremum | sql | readb-skill | 3 | 100% | 12,357 | 0.4914 | 12.2 | 6.0 | 3.0 |
| q7 | exact-phrase needle | files | readb-skill | 3 | 100% | 8,192 | 0.1778 | 5.1 | 2.0 | 0.0 |
| q8 | multi-hop | sql | readb-skill | 3 | 100% | 12,872 | 0.3981 | 13.3 | 5.0 | 2.0 |
| q9 | single-file lookup | files | readb-skill | 3 | 100% | 8,552 | 0.2680 | 8.9 | 3.0 | 0.0 |

## Cost ratio to baseline, by the shape a question was declared to favour

| arm | files (n=4) | neutral (n=1) | sql (n=7) |
|---|---|---|---|
| readb-skill | nan× | nan× | nan× |

## Integrity

| arm | runs | unsupported | skill fired | compacted | denials | readb never used |
|---|---|---|---|---|---|---|
| readb-skill | 36 | 0 | 28 | 0 | 0 | 11 |

Total reported spend: $4.05
