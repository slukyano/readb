# Benchmark results

144 runs recorded, 0 excluded as invalid, 144 used.

## Per arm, all questions pooled

| arm | n | exact | partial credit | new tokens ingested | cost, cache-neutral (USD) | wall clock (s) | output tokens | turns | cumulative prompt tokens |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 36 | 97% | 0.97 | 9,739 | 0.3698 | 11.4 | 453 | 4.0 | 120,302 |
| readb-bare | 36 | 94% | 0.94 | 9,542 | 0.2780 | 10.6 | 338 | 3.0 | 90,790 |
| readb-skill | 36 | 100% | 1.00 | 12,260 | 0.4925 | 14.4 | 604 | 6.0 | 161,637 |
| shell-coached | 36 | 100% | 1.00 | 9,051 | 0.3678 | 11.8 | 512 | 4.0 | 119,574 |

## Ratio to baseline, paired by question (below 1.00 favours the arm)

| arm | new tokens ingested [95% CI] | cost, cache-neutral (USD) [95% CI] | wall clock (s) [95% CI] | output tokens [95% CI] | turns [95% CI] | cumulative prompt tokens [95% CI] |
|---|---|---|---|---|---|---|
| readb-bare | 0.97× [0.85–1.02] | 0.76× [0.62–1.00] | 1.03× [0.70–1.20] | 0.65× [0.43–0.96] | 0.75× [0.62–1.00] | 0.76× [0.62–1.00] |
| readb-skill | 1.21× [1.00–1.35] | 1.21× [0.90–1.55] | 1.28× [0.89–1.38] | 0.99× [0.79–1.16] | 1.33× [1.00–1.75] | 1.22× [0.90–1.56] |
| shell-coached | 0.95× [0.91–0.97] | 0.99× [0.79–1.02] | 0.95× [0.79–1.16] | 0.98× [0.70–1.04] | 1.00× [0.79–1.00] | 1.00× [0.79–1.02] |

## By question shape

| question | shape | favours | arm | n | exact | ingested | cost (neutral) | wall (s) | turns | readb calls |
|---|---|---|---|---|---|---|---|---|---|---|
| q1 | type rollup | sql | baseline | 3 | 100% | 8,469 | 0.3595 | 11.5 | 4.0 | 0.0 |
| q1 | type rollup | sql | readb-bare | 3 | 100% | 9,445 | 0.2767 | 16.4 | 3.0 | 2.0 |
| q1 | type rollup | sql | readb-skill | 3 | 100% | 12,329 | 0.6985 | 20.2 | 8.0 | 2.0 |
| q1 | type rollup | sql | shell-coached | 3 | 100% | 8,430 | 0.2697 | 7.9 | 3.0 | 0.0 |
| q10 | malformed-file honesty | files | baseline | 3 | 100% | 17,349 | 0.5962 | 24.5 | 6.0 | 0.0 |
| q10 | malformed-file honesty | files | readb-bare | 3 | 100% | 10,153 | 0.7416 | 30.4 | 7.0 | 0.0 |
| q10 | malformed-file honesty | files | readb-skill | 3 | 100% | 11,795 | 0.6504 | 29.1 | 7.0 | 0.0 |
| q10 | malformed-file honesty | files | shell-coached | 3 | 100% | 8,592 | 0.2743 | 16.3 | 3.0 | 0.0 |
| q11 | fuzzy retrieval | files | baseline | 3 | 100% | 12,014 | 0.3745 | 10.7 | 4.0 | 0.0 |
| q11 | fuzzy retrieval | files | readb-bare | 3 | 100% | 11,801 | 0.2824 | 8.4 | 3.0 | 0.0 |
| q11 | fuzzy retrieval | files | readb-skill | 3 | 100% | 14,933 | 0.4996 | 14.0 | 6.0 | 1.0 |
| q11 | fuzzy retrieval | files | shell-coached | 3 | 100% | 11,686 | 0.3707 | 8.3 | 4.0 | 0.0 |
| q12 | five-part session | neutral | baseline | 3 | 100% | 9,604 | 0.3719 | 14.2 | 4.0 | 0.0 |
| q12 | five-part session | neutral | readb-bare | 3 | 100% | 9,602 | 0.2774 | 14.2 | 3.0 | 6.0 |
| q12 | five-part session | neutral | readb-skill | 3 | 100% | 13,405 | 0.7033 | 17.9 | 8.0 | 4.0 |
| q12 | five-part session | neutral | shell-coached | 3 | 100% | 9,260 | 0.3713 | 13.4 | 4.0 | 0.0 |
| q2 | group-by | sql | baseline | 3 | 100% | 8,757 | 0.2725 | 10.3 | 3.0 | 0.0 |
| q2 | group-by | sql | readb-bare | 3 | 100% | 9,544 | 0.3647 | 11.9 | 4.0 | 3.0 |
| q2 | group-by | sql | readb-skill | 3 | 100% | 11,342 | 0.2867 | 13.7 | 4.0 | 1.0 |
| q2 | group-by | sql | shell-coached | 3 | 100% | 8,380 | 0.2691 | 8.2 | 3.0 | 0.0 |
| q3 | filtered listing | sql | baseline | 3 | 100% | 10,297 | 0.5618 | 20.1 | 6.0 | 0.0 |
| q3 | filtered listing | sql | readb-bare | 3 | 100% | 9,540 | 0.2767 | 9.9 | 3.0 | 2.0 |
| q3 | filtered listing | sql | readb-skill | 3 | 100% | 15,068 | 0.7568 | 28.8 | 8.0 | 2.0 |
| q3 | filtered listing | sql | shell-coached | 3 | 100% | 9,434 | 0.4642 | 22.6 | 5.0 | 0.0 |
| q4 | cross-reference | sql | baseline | 3 | 100% | 12,071 | 0.9755 | 23.4 | 10.0 | 0.0 |
| q4 | cross-reference | sql | readb-bare | 3 | 100% | 9,807 | 0.3739 | 14.3 | 4.0 | 4.0 |
| q4 | cross-reference | sql | readb-skill | 3 | 100% | 11,971 | 0.3951 | 15.6 | 5.0 | 2.0 |
| q4 | cross-reference | sql | shell-coached | 3 | 100% | 10,429 | 0.6585 | 22.6 | 7.0 | 0.0 |
| q5 | list membership | sql | baseline | 3 | 100% | 10,755 | 0.2804 | 9.2 | 3.0 | 0.0 |
| q5 | list membership | sql | readb-bare | 3 | 100% | 9,483 | 0.2760 | 11.6 | 3.0 | 3.0 |
| q5 | list membership | sql | readb-skill | 3 | 100% | 12,708 | 0.4940 | 12.1 | 6.0 | 1.0 |
| q5 | list membership | sql | shell-coached | 3 | 100% | 9,617 | 0.3675 | 10.7 | 4.0 | 0.0 |
| q6 | extremum | sql | baseline | 3 | 67% | 9,742 | 0.3686 | 9.9 | 4.0 | 0.0 |
| q6 | extremum | sql | readb-bare | 3 | 33% | 9,294 | 0.2734 | 8.9 | 3.0 | 2.0 |
| q6 | extremum | sql | readb-skill | 3 | 100% | 12,267 | 0.4911 | 14.8 | 6.0 | 3.0 |
| q6 | extremum | sql | shell-coached | 3 | 100% | 8,966 | 0.4530 | 11.5 | 5.0 | 0.0 |
| q7 | exact-phrase needle | files | baseline | 3 | 100% | 8,078 | 0.1772 | 5.0 | 2.0 | 0.0 |
| q7 | exact-phrase needle | files | readb-bare | 3 | 100% | 8,167 | 0.1777 | 5.3 | 2.0 | 0.0 |
| q7 | exact-phrase needle | files | readb-skill | 3 | 100% | 8,186 | 0.1777 | 4.2 | 2.0 | 0.0 |
| q7 | exact-phrase needle | files | shell-coached | 3 | 100% | 8,202 | 0.1779 | 4.6 | 2.0 | 0.0 |
| q8 | multi-hop | sql | baseline | 3 | 100% | 14,026 | 0.8715 | 26.5 | 9.0 | 0.0 |
| q8 | multi-hop | sql | readb-bare | 3 | 100% | 9,622 | 0.2786 | 11.3 | 3.0 | 2.0 |
| q8 | multi-hop | sql | readb-skill | 3 | 100% | 13,226 | 0.5985 | 15.4 | 7.0 | 2.0 |
| q8 | multi-hop | sql | shell-coached | 3 | 100% | 13,266 | 0.8959 | 32.3 | 9.0 | 0.0 |
| q9 | single-file lookup | files | baseline | 3 | 100% | 9,052 | 0.3587 | 7.5 | 4.0 | 0.0 |
| q9 | single-file lookup | files | readb-bare | 3 | 100% | 9,276 | 0.3584 | 8.1 | 4.0 | 0.0 |
| q9 | single-file lookup | files | readb-skill | 3 | 100% | 9,398 | 0.2868 | 7.1 | 4.0 | 0.0 |
| q9 | single-file lookup | files | shell-coached | 3 | 100% | 8,617 | 0.3584 | 9.9 | 4.0 | 0.0 |

## Integrity

| arm | runs | unsupported | skill fired | compacted | denials | readb never used |
|---|---|---|---|---|---|---|
| baseline | 36 | 0 | 0 | 0 | 0 | 0 |
| readb-bare | 36 | 0 | 0 | 0 | 0 | 12 |
| readb-skill | 36 | 0 | 28 | 0 | 0 | 10 |
| shell-coached | 36 | 0 | 0 | 0 | 0 | 36 |

## Every wrong answer

- q6 baseline r3: answered `{'team-name': 31}` (partial 0.0)
- q6 readb-bare r2: answered `{'team-name': 31}` (partial 0.0)
- q6 readb-bare r3: answered `{'count': 31}` (partial 0.0)

Total reported spend: $16.51
