# Benchmark results

6 runs recorded, 0 excluded as invalid, 6 used.

## Per arm, all questions pooled

| arm | n | exact | partial credit | cost, as billed (USD) | cost, cache-neutral (USD) | new tokens ingested | wall clock (s) | output tokens | turns | cumulative prompt tokens |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 3 | 100% | 1.00 | 0.1976 | 0.5487 | 17,706 | 19.3 | 1,209 | 5.0 | 176,847 |
| readb-bare | 3 | 100% | 1.00 | 0.1282 | 0.4957 | 12,341 | 13.4 | 649 | 5.0 | 162,148 |

## Ratio to baseline, paired by question (below 1.00 favours the arm)

| arm | cost, as billed (USD) [95% CI] | cost, cache-neutral (USD) [95% CI] | new tokens ingested [95% CI] | wall clock (s) [95% CI] | output tokens [95% CI] | turns [95% CI] | cumulative prompt tokens [95% CI] |
|---|---|---|---|---|---|---|---|
| readb-bare | 0.65× | 0.90× | 0.70× | 0.69× | 0.54× | 1.00× | 0.92× |

## By question shape

| question | shape | favours | arm | n | exact | ingested | cost (neutral) | wall (s) | turns | readb calls |
|---|---|---|---|---|---|---|---|---|---|---|
| q10b | malformed count, tabular phrasing | files | baseline | 3 | 100% | 17,706 | 0.5487 | 19.3 | 5.0 | 0.0 |
| q10b | malformed count, tabular phrasing | files | readb-bare | 3 | 100% | 12,341 | 0.4957 | 13.4 | 5.0 | 2.0 |

## Cost ratio to baseline, by the shape a question was declared to favour

| arm | files (n=1) |
|---|---|
| readb-bare | 0.65× |

## Integrity

| arm | runs | unsupported | skill fired | compacted | denials | readb never used |
|---|---|---|---|---|---|---|
| baseline | 3 | 0 | 0 | 0 | 0 | 0 |
| readb-bare | 3 | 0 | 0 | 0 | 0 | 0 |

Total reported spend: $0.61
