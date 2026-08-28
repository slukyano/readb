# Benchmark results — v3

702 runs recorded, 1 excluded as invalid, 701 used.
Models: claude-haiku-4-5, claude-sonnet-5. Arms: baseline, readb-bare, readb-cached, readb-skill, shell-coached. Questions: 26.

## Pre-registered endpoints

| id | contrast | model | questions | effect | p | Holm p | test |
|---|---|---|---|---|---|---|---|
| E1 | readb-cached vs readb-bare, billed cost, backlog stratum | sonnet-5 | 8 | 1.00x [0.98–1.07] | 0.5469 | 1.0000 | exact (256 sign assignments) |
| E3 | readb-cached vs shell-coached, billed cost, join stratum | sonnet-5 | 8 | 1.04x [0.71–1.34] | 0.9453 | 1.0000 | exact (256 sign assignments) |

| E2 | skill invocation rate, `readb-skill` vs v2's 37/78 | sonnet-5 | 78 runs | 44/78 = 56% | 0.3363 | 1.0000 | Fisher exact |

- **E1** — the cache's own contrast: two arms with identical preambles, differing only in whether the bundle is a registry with a warm cache. Parity is the predicted outcome, recorded as such in the pre-registration.
- **E3** — readb at its best against the honest competitor, carried forward from v2's E1.
- **E2** — whether the description rewritten in sprint-006 is found more often than the one v2 measured. Read with the confounds in the write-up: v3's skill arm also runs against a primed cache, the skill's body changed, and the runtime moved between batteries.

## claude-haiku-4-5

### Per arm, all questions pooled

| arm | n | exact | partial | answer parsed | cost, as billed (USD) | new tokens ingested | turns | cumulative prompt tokens |
|---|---|---|---|---|---|---|---|---|
| baseline | 78 | 77% | 0.84 | 100% | 0.0520 | 11,702 | 9.0 | 210,022 |
| readb-bare | 78 | 94% | 0.94 | 100% | 0.0318 | 8,628 | 4.0 | 94,545 |
| readb-cached | 78 | 92% | 0.93 | 100% | 0.0307 | 8,558 | 4.0 | 94,040 |
| shell-coached | 78 | 92% | 0.94 | 100% | 0.0307 | 8,372 | 4.0 | 93,384 |

### Ratio to `baseline`, paired by question (below 1.00 favours the arm)

| arm | cost, as billed (USD) [95% CI] | new tokens ingested [95% CI] | turns [95% CI] | cumulative prompt tokens [95% CI] |
|---|---|---|---|---|
| readb-bare | 0.69x [0.46–0.91] | 0.80x [0.67–0.96] | 0.67x [0.44–0.85] | 0.56x [0.37–0.83] |
| readb-cached | 0.69x [0.53–0.83] | 0.82x [0.65–0.96] | 0.58x [0.46–0.77] | 0.58x [0.43–0.73] |
| readb-skill | — | — | — | — |
| shell-coached | 0.71x [0.50–0.84] | 0.83x [0.70–0.90] | 0.59x [0.37–0.71] | 0.53x [0.32–0.77] |

### Billed-cost ratio to `baseline` by stratum

| arm | backlog (n=8) | hazard (n=3) | join (n=8) | retrieval (n=3) | scan (n=4) |
|---|---|---|---|---|---|
| readb-bare | 0.69x | 0.90x | 0.38x | 0.98x | 0.70x |
| readb-cached | 0.78x | 0.76x | 0.40x | 1.01x | 0.62x |
| readb-skill | — | — | — | — | — |
| shell-coached | 0.77x | 0.69x | 0.48x | 1.02x | 0.57x |

### Tool choice — what the agent reached for, against what a question declares

A result, never a reason to edit a prompt. `match` is the share of runs whose chosen tool equalled the question's declared expert tool.

| arm | readb | shell | read | other | none | match | failed calls | failed readb |
|---|---|---|---|---|---|---|---|---|
| baseline | 0 | 73 | 5 | 0 | 0 | 19% | 59 | 0 |
| readb-bare | 62 | 14 | 2 | 0 | 0 | 74% | 17 | 12 |
| readb-cached | 62 | 14 | 2 | 0 | 0 | 76% | 15 | 10 |
| shell-coached | 0 | 75 | 3 | 0 | 0 | 19% | 35 | 0 |

## claude-sonnet-5

### Per arm, all questions pooled

| arm | n | exact | partial | answer parsed | cost, as billed (USD) | new tokens ingested | turns | cumulative prompt tokens |
|---|---|---|---|---|---|---|---|---|
| baseline | 77 | 88% | 0.91 | 100% | 0.0969 | 12,277 | 6.0 | 186,452 |
| readb-bare | 78 | 100% | 1.00 | 100% | 0.0688 | 10,285 | 4.0 | 123,386 |
| readb-cached | 78 | 99% | 0.99 | 100% | 0.0688 | 10,314 | 4.0 | 122,884 |
| readb-skill | 78 | 95% | 0.98 | 100% | 0.0800 | 12,377 | 5.0 | 132,753 |
| shell-coached | 78 | 96% | 0.96 | 100% | 0.0667 | 9,819 | 3.0 | 95,260 |

### Ratio to `baseline`, paired by question (below 1.00 favours the arm)

| arm | cost, as billed (USD) [95% CI] | new tokens ingested [95% CI] | turns [95% CI] | cumulative prompt tokens [95% CI] |
|---|---|---|---|---|
| readb-bare | 0.74x [0.56–0.90] | 0.93x [0.79–1.01] | 0.60x [0.47–1.00] | 0.59x [0.48–0.93] |
| readb-cached | 0.68x [0.55–0.90] | 0.92x [0.80–1.00] | 0.60x [0.45–0.88] | 0.61x [0.45–0.84] |
| readb-skill | 0.91x [0.69–1.02] | 0.98x [0.84–1.15] | 1.00x [0.76–1.00] | 0.79x [0.69–0.94] |
| shell-coached | 0.67x [0.60–0.79] | 0.87x [0.77–0.96] | 0.60x [0.50–0.71] | 0.59x [0.47–0.67] |

### Billed-cost ratio to `baseline` by stratum

| arm | backlog (n=8) | hazard (n=3) | join (n=8) | retrieval (n=3) | scan (n=4) |
|---|---|---|---|---|---|
| readb-bare | 0.89x | 0.53x | 0.61x | 1.01x | 0.74x |
| readb-cached | 0.88x | 0.53x | 0.58x | 1.01x | 0.70x |
| readb-skill | 0.92x | 0.61x | 0.69x | 1.13x | 1.01x |
| shell-coached | 0.75x | 0.48x | 0.60x | 1.02x | 0.74x |

### Tool choice — what the agent reached for, against what a question declares

A result, never a reason to edit a prompt. `match` is the share of runs whose chosen tool equalled the question's declared expert tool.

| arm | readb | shell | read | other | none | match | failed calls | failed readb |
|---|---|---|---|---|---|---|---|---|
| baseline | 0 | 76 | 1 | 0 | 0 | 16% | 58 | 0 |
| readb-bare | 67 | 11 | 0 | 0 | 0 | 79% | 16 | 16 |
| readb-cached | 64 | 14 | 0 | 0 | 0 | 78% | 14 | 10 |
| readb-skill | 44 | 33 | 1 | 0 | 0 | 54% | 20 | 3 |
| shell-coached | 0 | 74 | 4 | 0 | 0 | 19% | 16 | 0 |


### The cache — `readb-cached` against `readb-bare`

sonnet-5, backlog stratum. Identical preambles; the corpus is a registry with a primed cache.

| measure | ratio, cached/bare | questions |
| --- | --- | --- |
| billed cost | 1.00x | 8 |
| wall clock (declared secondary) | 0.89x | 8 |

**The wall-clock figure cannot be read as the cache's effect.** Arms run in a fixed order within every cell, and `readb-cached` always runs immediately after `readb-bare`. v2's `readb-bare` vs `readb-nudged` pair — both uncached, adjacent in the same way — shows a median wall ratio of 0.94 favouring the later arm on Sonnet with no treatment present at all. Any wall-clock effect smaller than that is indistinguishable from running second. The cache's speed is established by direct measurement of readb itself, reported in the write-up, not by this contrast.

## The malformed-file hazard

`saw warning` counts runs where readb's skip warning reached the transcript. A wrong answer with the warning seen and a wrong answer without it are different findings: the first says the warning did not work, the second says the hazard is silent.

| model | arm | question | n | exact | saw warning | tool |
|---|---|---|---|---|---|---|
| haiku-4-5 | baseline | q10 | 3 | 100% | 0/3 | shell |
| haiku-4-5 | baseline | q10b | 3 | 100% | 0/3 | shell |
| haiku-4-5 | baseline | q18 | 3 | 100% | 0/3 | shell |
| haiku-4-5 | readb-bare | q10 | 3 | 100% | 0/3 | shell |
| haiku-4-5 | readb-bare | q10b | 3 | 100% | 2/3 | readb/shell |
| haiku-4-5 | readb-bare | q18 | 3 | 0% | 3/3 | readb |
| haiku-4-5 | readb-cached | q10 | 3 | 100% | 0/3 | shell |
| haiku-4-5 | readb-cached | q10b | 3 | 100% | 3/3 | readb |
| haiku-4-5 | readb-cached | q18 | 3 | 0% | 3/3 | readb |
| haiku-4-5 | shell-coached | q10 | 3 | 100% | 0/3 | shell |
| haiku-4-5 | shell-coached | q10b | 3 | 100% | 0/3 | shell |
| haiku-4-5 | shell-coached | q18 | 3 | 33% | 0/3 | shell |
| sonnet-5 | baseline | q10 | 3 | 100% | 0/3 | shell |
| sonnet-5 | baseline | q10b | 3 | 100% | 0/3 | shell |
| sonnet-5 | baseline | q18 | 3 | 100% | 0/3 | shell |
| sonnet-5 | readb-bare | q10 | 3 | 100% | 0/3 | shell |
| sonnet-5 | readb-bare | q10b | 3 | 100% | 3/3 | readb |
| sonnet-5 | readb-bare | q18 | 3 | 100% | 3/3 | readb |
| sonnet-5 | readb-cached | q10 | 3 | 100% | 0/3 | shell |
| sonnet-5 | readb-cached | q10b | 3 | 100% | 3/3 | readb |
| sonnet-5 | readb-cached | q18 | 3 | 67% | 3/3 | readb |
| sonnet-5 | readb-skill | q10 | 3 | 100% | 0/3 | shell |
| sonnet-5 | readb-skill | q10b | 3 | 100% | 3/3 | readb |
| sonnet-5 | readb-skill | q18 | 3 | 100% | 3/3 | readb |
| sonnet-5 | shell-coached | q10 | 3 | 100% | 0/3 | shell |
| sonnet-5 | shell-coached | q10b | 3 | 100% | 0/3 | shell |
| sonnet-5 | shell-coached | q18 | 3 | 100% | 0/3 | shell |

## By question

| question | stratum | shape | expert | model | arm | n | exact | ingested | cost (billed) | turns | readb calls |
|---|---|---|---|---|---|---|---|---|---|---|---|
| b1 | backlog | ready-to-schedule | readb | haiku-4-5 | baseline | 3 | 33% | 12,558 | 0.0635 | 9.0 | 0.0 |
| b1 | backlog | ready-to-schedule | readb | haiku-4-5 | readb-bare | 3 | 100% | 8,863 | 0.0368 | 4.0 | 3.0 |
| b1 | backlog | ready-to-schedule | readb | haiku-4-5 | readb-cached | 3 | 100% | 13,865 | 0.0535 | 5.0 | 4.0 |
| b1 | backlog | ready-to-schedule | readb | haiku-4-5 | shell-coached | 3 | 67% | 11,718 | 0.0643 | 9.0 | 0.0 |
| b1 | backlog | ready-to-schedule | readb | sonnet-5 | baseline | 3 | 100% | 15,782 | 0.2039 | 16.0 | 0.0 |
| b1 | backlog | ready-to-schedule | readb | sonnet-5 | readb-bare | 3 | 100% | 14,737 | 0.0925 | 3.0 | 2.0 |
| b1 | backlog | ready-to-schedule | readb | sonnet-5 | readb-cached | 3 | 100% | 16,700 | 0.1173 | 5.0 | 4.0 |
| b1 | backlog | ready-to-schedule | readb | sonnet-5 | readb-skill | 3 | 100% | 14,325 | 0.1149 | 8.0 | 5.0 |
| b1 | backlog | ready-to-schedule | readb | sonnet-5 | shell-coached | 3 | 100% | 14,714 | 0.1005 | 3.0 | 0.0 |
| b2 | backlog | active sprint scope + design approach | readb | haiku-4-5 | baseline | 3 | 100% | 11,420 | 0.0463 | 9.0 | 0.0 |
| b2 | backlog | active sprint scope + design approach | readb | haiku-4-5 | readb-bare | 3 | 100% | 8,818 | 0.0318 | 7.0 | 2.0 |
| b2 | backlog | active sprint scope + design approach | readb | haiku-4-5 | readb-cached | 3 | 100% | 8,565 | 0.0303 | 6.0 | 2.0 |
| b2 | backlog | active sprint scope + design approach | readb | haiku-4-5 | shell-coached | 3 | 100% | 10,128 | 0.0425 | 7.0 | 0.0 |
| b2 | backlog | active sprint scope + design approach | readb | sonnet-5 | baseline | 3 | 100% | 12,632 | 0.1011 | 9.0 | 0.0 |
| b2 | backlog | active sprint scope + design approach | readb | sonnet-5 | readb-bare | 3 | 100% | 10,512 | 0.0690 | 4.0 | 4.0 |
| b2 | backlog | active sprint scope + design approach | readb | sonnet-5 | readb-cached | 3 | 100% | 10,503 | 0.0688 | 4.0 | 4.0 |
| b2 | backlog | active sprint scope + design approach | readb | sonnet-5 | readb-skill | 3 | 100% | 12,118 | 0.0908 | 6.0 | 0.0 |
| b2 | backlog | active sprint scope + design approach | readb | sonnet-5 | shell-coached | 3 | 100% | 10,475 | 0.0777 | 5.0 | 0.0 |
| b3 | backlog | delivered from a finished sprint | readb | haiku-4-5 | baseline | 3 | 67% | 12,231 | 0.0575 | 13.0 | 0.0 |
| b3 | backlog | delivered from a finished sprint | readb | haiku-4-5 | readb-bare | 3 | 100% | 8,257 | 0.0333 | 5.0 | 0.0 |
| b3 | backlog | delivered from a finished sprint | readb | haiku-4-5 | readb-cached | 3 | 100% | 8,552 | 0.0351 | 6.0 | 2.0 |
| b3 | backlog | delivered from a finished sprint | readb | haiku-4-5 | shell-coached | 3 | 100% | 9,749 | 0.0448 | 8.0 | 0.0 |
| b3 | backlog | delivered from a finished sprint | readb | sonnet-5 | baseline | 3 | 100% | 9,221 | 0.0631 | 4.0 | 0.0 |
| b3 | backlog | delivered from a finished sprint | readb | sonnet-5 | readb-bare | 3 | 100% | 9,465 | 0.0706 | 5.0 | 4.0 |
| b3 | backlog | delivered from a finished sprint | readb | sonnet-5 | readb-cached | 3 | 100% | 10,180 | 0.0758 | 5.0 | 0.0 |
| b3 | backlog | delivered from a finished sprint | readb | sonnet-5 | readb-skill | 3 | 100% | 12,412 | 0.0770 | 5.0 | 2.0 |
| b3 | backlog | delivered from a finished sprint | readb | sonnet-5 | shell-coached | 3 | 100% | 9,439 | 0.0638 | 4.0 | 0.0 |
| b4 | backlog | open work touching a feature | readb | haiku-4-5 | baseline | 3 | 100% | 9,000 | 0.0365 | 5.0 | 0.0 |
| b4 | backlog | open work touching a feature | readb | haiku-4-5 | readb-bare | 3 | 100% | 7,683 | 0.0251 | 3.0 | 2.0 |
| b4 | backlog | open work touching a feature | readb | haiku-4-5 | readb-cached | 3 | 100% | 8,306 | 0.0270 | 3.0 | 2.0 |
| b4 | backlog | open work touching a feature | readb | haiku-4-5 | shell-coached | 3 | 100% | 7,984 | 0.0281 | 3.0 | 0.0 |
| b4 | backlog | open work touching a feature | readb | sonnet-5 | baseline | 3 | 100% | 11,976 | 0.1109 | 8.0 | 0.0 |
| b4 | backlog | open work touching a feature | readb | sonnet-5 | readb-bare | 3 | 100% | 9,645 | 0.0583 | 3.0 | 2.0 |
| b4 | backlog | open work touching a feature | readb | sonnet-5 | readb-cached | 3 | 100% | 9,651 | 0.0585 | 3.0 | 2.0 |
| b4 | backlog | open work touching a feature | readb | sonnet-5 | readb-skill | 3 | 100% | 10,311 | 0.0769 | 4.0 | 0.0 |
| b4 | backlog | open work touching a feature | readb | sonnet-5 | shell-coached | 3 | 100% | 10,414 | 0.0746 | 4.0 | 0.0 |
| b5 | backlog | single-task lookup | read | haiku-4-5 | baseline | 3 | 67% | 7,735 | 0.0268 | 4.0 | 0.0 |
| b5 | backlog | single-task lookup | read | haiku-4-5 | readb-bare | 3 | 100% | 9,144 | 0.0415 | 8.0 | 7.0 |
| b5 | backlog | single-task lookup | read | haiku-4-5 | readb-cached | 3 | 100% | 9,438 | 0.0366 | 6.0 | 4.0 |
| b5 | backlog | single-task lookup | read | haiku-4-5 | shell-coached | 3 | 100% | 7,885 | 0.0304 | 5.0 | 0.0 |
| b5 | backlog | single-task lookup | read | sonnet-5 | baseline | 3 | 100% | 8,766 | 0.0534 | 3.0 | 0.0 |
| b5 | backlog | single-task lookup | read | sonnet-5 | readb-bare | 3 | 100% | 9,206 | 0.0571 | 3.0 | 2.0 |
| b5 | backlog | single-task lookup | read | sonnet-5 | readb-cached | 3 | 100% | 9,570 | 0.0574 | 3.0 | 3.0 |
| b5 | backlog | single-task lookup | read | sonnet-5 | readb-skill | 3 | 100% | 11,907 | 0.0667 | 4.0 | 2.0 |
| b5 | backlog | single-task lookup | read | sonnet-5 | shell-coached | 3 | 100% | 9,040 | 0.0549 | 3.0 | 0.0 |
| b6 | backlog | dropped-task digest | readb | haiku-4-5 | baseline | 3 | 33% | 15,101 | 0.0728 | 11.0 | 0.0 |
| b6 | backlog | dropped-task digest | readb | haiku-4-5 | readb-bare | 3 | 100% | 9,689 | 0.0337 | 9.0 | 2.0 |
| b6 | backlog | dropped-task digest | readb | haiku-4-5 | readb-cached | 3 | 100% | 8,158 | 0.0265 | 3.0 | 2.0 |
| b6 | backlog | dropped-task digest | readb | haiku-4-5 | shell-coached | 3 | 100% | 9,878 | 0.0464 | 7.0 | 0.0 |
| b6 | backlog | dropped-task digest | readb | sonnet-5 | baseline | 3 | 33% | 10,273 | 0.0799 | 5.0 | 0.0 |
| b6 | backlog | dropped-task digest | readb | sonnet-5 | readb-bare | 3 | 100% | 10,416 | 0.0692 | 4.0 | 3.0 |
| b6 | backlog | dropped-task digest | readb | sonnet-5 | readb-cached | 3 | 100% | 10,441 | 0.0694 | 4.0 | 3.0 |
| b6 | backlog | dropped-task digest | readb | sonnet-5 | readb-skill | 3 | 67% | 13,002 | 0.0815 | 5.0 | 1.0 |
| b6 | backlog | dropped-task digest | readb | sonnet-5 | shell-coached | 3 | 100% | 10,697 | 0.0831 | 5.0 | 0.0 |
| b7 | backlog | next free number | readb | haiku-4-5 | baseline | 3 | 33% | 7,476 | 0.0279 | 4.0 | 0.0 |
| b7 | backlog | next free number | readb | haiku-4-5 | readb-bare | 3 | 33% | 7,936 | 0.0278 | 5.0 | 0.0 |
| b7 | backlog | next free number | readb | haiku-4-5 | readb-cached | 3 | 33% | 7,391 | 0.0230 | 3.0 | 0.0 |
| b7 | backlog | next free number | readb | haiku-4-5 | shell-coached | 3 | 100% | 7,216 | 0.0205 | 2.0 | 0.0 |
| b7 | backlog | next free number | readb | sonnet-5 | baseline | 3 | 33% | 12,605 | 0.0773 | 4.0 | 0.0 |
| b7 | backlog | next free number | readb | sonnet-5 | readb-bare | 3 | 100% | 13,752 | 0.0885 | 5.0 | 4.0 |
| b7 | backlog | next free number | readb | sonnet-5 | readb-cached | 3 | 100% | 12,178 | 0.0819 | 5.0 | 4.0 |
| b7 | backlog | next free number | readb | sonnet-5 | readb-skill | 3 | 67% | 9,941 | 0.0641 | 4.0 | 0.0 |
| b7 | backlog | next free number | readb | sonnet-5 | shell-coached | 3 | 100% | 9,083 | 0.0560 | 3.0 | 0.0 |
| b8 | backlog | tag rollup | readb | haiku-4-5 | baseline | 3 | 0% | 14,747 | 0.0554 | 8.0 | 0.0 |
| b8 | backlog | tag rollup | readb | haiku-4-5 | readb-bare | 3 | 100% | 14,168 | 0.0795 | 14.0 | 6.0 |
| b8 | backlog | tag rollup | readb | haiku-4-5 | readb-cached | 3 | 100% | 9,652 | 0.0468 | 8.0 | 7.0 |
| b8 | backlog | tag rollup | readb | haiku-4-5 | shell-coached | 3 | 67% | 7,883 | 0.0277 | 4.0 | 0.0 |
| b8 | backlog | tag rollup | readb | sonnet-5 | baseline | 3 | 0% | 9,549 | 0.0723 | 4.0 | 0.0 |
| b8 | backlog | tag rollup | readb | sonnet-5 | readb-bare | 3 | 100% | 9,796 | 0.0664 | 4.0 | 4.0 |
| b8 | backlog | tag rollup | readb | sonnet-5 | readb-cached | 3 | 100% | 9,568 | 0.0648 | 4.0 | 3.0 |
| b8 | backlog | tag rollup | readb | sonnet-5 | readb-skill | 3 | 100% | 12,028 | 0.0681 | 4.0 | 1.0 |
| b8 | backlog | tag rollup | readb | sonnet-5 | shell-coached | 3 | 0% | 8,818 | 0.0473 | 2.0 | 0.0 |
| q1 | scan | type rollup | readb | haiku-4-5 | baseline | 3 | 100% | 8,767 | 0.0359 | 6.0 | 0.0 |
| q1 | scan | type rollup | readb | haiku-4-5 | readb-bare | 3 | 100% | 8,634 | 0.0361 | 6.0 | 2.0 |
| q1 | scan | type rollup | readb | haiku-4-5 | readb-cached | 3 | 100% | 7,838 | 0.0247 | 3.0 | 2.0 |
| q1 | scan | type rollup | readb | haiku-4-5 | shell-coached | 3 | 100% | 7,611 | 0.0237 | 2.0 | 0.0 |
| q1 | scan | type rollup | readb | sonnet-5 | baseline | 3 | 100% | 9,026 | 0.0692 | 5.0 | 0.0 |
| q1 | scan | type rollup | readb | sonnet-5 | readb-bare | 3 | 100% | 10,283 | 0.0623 | 3.0 | 5.0 |
| q1 | scan | type rollup | readb | sonnet-5 | readb-cached | 3 | 100% | 10,292 | 0.0625 | 3.0 | 5.0 |
| q1 | scan | type rollup | readb | sonnet-5 | readb-skill | 3 | 100% | 12,108 | 0.0756 | 5.0 | 2.0 |
| q1 | scan | type rollup | readb | sonnet-5 | shell-coached | 3 | 100% | 8,924 | 0.0546 | 3.0 | 0.0 |
| q10 | hazard | malformed-file honesty, warned | shell | haiku-4-5 | baseline | 3 | 100% | 11,609 | 0.0517 | 8.0 | 0.0 |
| q10 | hazard | malformed-file honesty, warned | shell | haiku-4-5 | readb-bare | 3 | 100% | 10,251 | 0.0467 | 5.0 | 0.0 |
| q10 | hazard | malformed-file honesty, warned | shell | haiku-4-5 | readb-cached | 3 | 100% | 10,106 | 0.0394 | 4.0 | 0.0 |
| q10 | hazard | malformed-file honesty, warned | shell | haiku-4-5 | shell-coached | 3 | 100% | 9,355 | 0.0359 | 2.0 | 0.0 |
| q10 | hazard | malformed-file honesty, warned | shell | sonnet-5 | baseline | 3 | 100% | 11,277 | 0.0969 | 6.0 | 0.0 |
| q10 | hazard | malformed-file honesty, warned | shell | sonnet-5 | readb-bare | 3 | 100% | 9,973 | 0.0769 | 3.0 | 0.0 |
| q10 | hazard | malformed-file honesty, warned | shell | sonnet-5 | readb-cached | 3 | 100% | 9,205 | 0.0661 | 4.0 | 0.0 |
| q10 | hazard | malformed-file honesty, warned | shell | sonnet-5 | readb-skill | 3 | 100% | 9,122 | 0.0589 | 3.0 | 0.0 |
| q10 | hazard | malformed-file honesty, warned | shell | sonnet-5 | shell-coached | 3 | 100% | 9,933 | 0.0790 | 4.0 | 0.0 |
| q10b | hazard | malformed count, tabular phrasing | shell | haiku-4-5 | baseline | 3 | 100% | 9,298 | 0.0338 | 6.0 | 0.0 |
| q10b | hazard | malformed count, tabular phrasing | shell | haiku-4-5 | readb-bare | 3 | 100% | 10,471 | 0.0387 | 5.0 | 2.0 |
| q10b | hazard | malformed count, tabular phrasing | shell | haiku-4-5 | readb-cached | 3 | 100% | 10,775 | 0.0398 | 5.0 | 2.0 |
| q10b | hazard | malformed count, tabular phrasing | shell | haiku-4-5 | shell-coached | 3 | 100% | 9,024 | 0.0384 | 6.0 | 0.0 |
| q10b | hazard | malformed count, tabular phrasing | shell | sonnet-5 | baseline | 3 | 100% | 21,145 | 0.2251 | 12.0 | 0.0 |
| q10b | hazard | malformed count, tabular phrasing | shell | sonnet-5 | readb-bare | 3 | 100% | 11,852 | 0.0810 | 4.0 | 4.0 |
| q10b | hazard | malformed count, tabular phrasing | shell | sonnet-5 | readb-cached | 3 | 100% | 13,436 | 0.0773 | 4.0 | 2.0 |
| q10b | hazard | malformed count, tabular phrasing | shell | sonnet-5 | readb-skill | 3 | 100% | 15,076 | 0.0998 | 6.0 | 3.0 |
| q10b | hazard | malformed count, tabular phrasing | shell | sonnet-5 | shell-coached | 3 | 100% | 11,171 | 0.0868 | 5.0 | 0.0 |
| q11 | retrieval | fuzzy retrieval | read | haiku-4-5 | baseline | 3 | 67% | 12,178 | 0.0539 | 8.0 | 0.0 |
| q11 | retrieval | fuzzy retrieval | read | haiku-4-5 | readb-bare | 3 | 100% | 10,807 | 0.0399 | 8.0 | 0.0 |
| q11 | retrieval | fuzzy retrieval | read | haiku-4-5 | readb-cached | 3 | 100% | 11,592 | 0.0448 | 9.0 | 0.0 |
| q11 | retrieval | fuzzy retrieval | read | haiku-4-5 | shell-coached | 3 | 100% | 15,095 | 0.0731 | 10.0 | 0.0 |
| q11 | retrieval | fuzzy retrieval | read | sonnet-5 | baseline | 3 | 100% | 11,988 | 0.0676 | 3.0 | 0.0 |
| q11 | retrieval | fuzzy retrieval | read | sonnet-5 | readb-bare | 3 | 100% | 12,086 | 0.0678 | 3.0 | 0.0 |
| q11 | retrieval | fuzzy retrieval | read | sonnet-5 | readb-cached | 3 | 100% | 12,250 | 0.0752 | 4.0 | 0.0 |
| q11 | retrieval | fuzzy retrieval | read | sonnet-5 | readb-skill | 3 | 100% | 12,384 | 0.0761 | 4.0 | 0.0 |
| q11 | retrieval | fuzzy retrieval | read | sonnet-5 | shell-coached | 3 | 100% | 12,359 | 0.0691 | 3.0 | 0.0 |
| q12 | join | five-part session | readb | haiku-4-5 | baseline | 3 | 33% | 16,198 | 0.0955 | 15.0 | 0.0 |
| q12 | join | five-part session | readb | haiku-4-5 | readb-bare | 3 | 100% | 8,540 | 0.0285 | 7.0 | 6.0 |
| q12 | join | five-part session | readb | haiku-4-5 | readb-cached | 3 | 100% | 8,454 | 0.0279 | 7.0 | 6.0 |
| q12 | join | five-part session | readb | haiku-4-5 | shell-coached | 3 | 67% | 8,050 | 0.0265 | 6.0 | 0.0 |
| q12 | join | five-part session | readb | sonnet-5 | baseline | 3 | 67% | 10,884 | 0.0962 | 7.0 | 0.0 |
| q12 | join | five-part session | readb | sonnet-5 | readb-bare | 3 | 100% | 10,179 | 0.0605 | 3.0 | 6.0 |
| q12 | join | five-part session | readb | sonnet-5 | readb-cached | 3 | 100% | 10,192 | 0.0606 | 3.0 | 6.0 |
| q12 | join | five-part session | readb | sonnet-5 | readb-skill | 3 | 100% | 13,892 | 0.0923 | 6.0 | 3.0 |
| q12 | join | five-part session | readb | sonnet-5 | shell-coached | 3 | 100% | 9,251 | 0.0592 | 3.0 | 0.0 |
| q14 | join | body + frontmatter hybrid | readb | haiku-4-5 | baseline | 3 | 100% | 10,665 | 0.0459 | 9.0 | 0.0 |
| q14 | join | body + frontmatter hybrid | readb | haiku-4-5 | readb-bare | 3 | 100% | 28,080 | 0.0930 | 8.0 | 2.0 |
| q14 | join | body + frontmatter hybrid | readb | haiku-4-5 | readb-cached | 3 | 67% | 11,870 | 0.0538 | 9.0 | 2.0 |
| q14 | join | body + frontmatter hybrid | readb | haiku-4-5 | shell-coached | 3 | 100% | 9,127 | 0.0400 | 7.0 | 0.0 |
| q14 | join | body + frontmatter hybrid | readb | sonnet-5 | baseline | 3 | 100% | 14,212 | 0.1332 | 10.0 | 0.0 |
| q14 | join | body + frontmatter hybrid | readb | sonnet-5 | readb-bare | 3 | 100% | 10,636 | 0.0848 | 6.0 | 4.0 |
| q14 | join | body + frontmatter hybrid | readb | sonnet-5 | readb-cached | 3 | 100% | 11,055 | 0.0856 | 6.0 | 4.0 |
| q14 | join | body + frontmatter hybrid | readb | sonnet-5 | readb-skill | 3 | 33% | 10,188 | 0.0773 | 5.0 | 0.0 |
| q14 | join | body + frontmatter hybrid | readb | sonnet-5 | shell-coached | 3 | 100% | 9,352 | 0.0508 | 2.0 | 0.0 |
| q15 | scan | output-heavy enumeration | readb | haiku-4-5 | baseline | 3 | 67% | 11,966 | 0.0656 | 11.0 | 0.0 |
| q15 | scan | output-heavy enumeration | readb | haiku-4-5 | readb-bare | 3 | 100% | 8,559 | 0.0290 | 3.0 | 2.0 |
| q15 | scan | output-heavy enumeration | readb | haiku-4-5 | readb-cached | 3 | 100% | 8,550 | 0.0290 | 3.0 | 2.0 |
| q15 | scan | output-heavy enumeration | readb | haiku-4-5 | shell-coached | 3 | 100% | 9,127 | 0.0303 | 3.0 | 0.0 |
| q15 | scan | output-heavy enumeration | readb | sonnet-5 | baseline | 3 | 100% | 16,260 | 0.1214 | 7.0 | 0.0 |
| q15 | scan | output-heavy enumeration | readb | sonnet-5 | readb-bare | 3 | 100% | 10,829 | 0.0708 | 3.0 | 3.0 |
| q15 | scan | output-heavy enumeration | readb | sonnet-5 | readb-cached | 3 | 100% | 10,813 | 0.0698 | 3.0 | 2.0 |
| q15 | scan | output-heavy enumeration | readb | sonnet-5 | readb-skill | 3 | 100% | 14,754 | 0.1115 | 7.0 | 0.0 |
| q15 | scan | output-heavy enumeration | readb | sonnet-5 | shell-coached | 3 | 100% | 11,510 | 0.0830 | 4.0 | 0.0 |
| q16 | join | zero result | readb | haiku-4-5 | baseline | 3 | 100% | 15,670 | 0.0864 | 12.0 | 0.0 |
| q16 | join | zero result | readb | haiku-4-5 | readb-bare | 3 | 100% | 8,504 | 0.0307 | 4.0 | 3.0 |
| q16 | join | zero result | readb | haiku-4-5 | readb-cached | 3 | 100% | 8,577 | 0.0311 | 4.0 | 3.0 |
| q16 | join | zero result | readb | haiku-4-5 | shell-coached | 3 | 100% | 10,313 | 0.0459 | 7.0 | 0.0 |
| q16 | join | zero result | readb | sonnet-5 | baseline | 3 | 100% | 16,014 | 0.1575 | 10.0 | 0.0 |
| q16 | join | zero result | readb | sonnet-5 | readb-bare | 3 | 100% | 10,863 | 0.0697 | 4.0 | 4.0 |
| q16 | join | zero result | readb | sonnet-5 | readb-cached | 3 | 100% | 10,753 | 0.0712 | 4.0 | 4.0 |
| q16 | join | zero result | readb | sonnet-5 | readb-skill | 3 | 100% | 13,751 | 0.1070 | 8.0 | 6.0 |
| q16 | join | zero result | readb | sonnet-5 | shell-coached | 3 | 100% | 12,016 | 0.0893 | 6.0 | 0.0 |
| q17 | scan | false presupposition | readb | haiku-4-5 | baseline | 3 | 100% | 17,672 | 0.1363 | 28.0 | 0.0 |
| q17 | scan | false presupposition | readb | haiku-4-5 | readb-bare | 3 | 100% | 17,414 | 0.1147 | 22.0 | 5.0 |
| q17 | scan | false presupposition | readb | haiku-4-5 | readb-cached | 3 | 100% | 18,941 | 0.1197 | 18.0 | 4.0 |
| q17 | scan | false presupposition | readb | haiku-4-5 | shell-coached | 3 | 100% | 17,474 | 0.1035 | 17.0 | 0.0 |
| q17 | scan | false presupposition | readb | sonnet-5 | baseline | 2 | 100% | 14,676 | 0.1694 | 13.5 | 0.0 |
| q17 | scan | false presupposition | readb | sonnet-5 | readb-bare | 3 | 100% | 17,887 | 0.2191 | 16.0 | 9.0 |
| q17 | scan | false presupposition | readb | sonnet-5 | readb-cached | 3 | 100% | 15,028 | 0.1386 | 10.0 | 2.0 |
| q17 | scan | false presupposition | readb | sonnet-5 | readb-skill | 3 | 100% | 18,973 | 0.2378 | 20.0 | 0.0 |
| q17 | scan | false presupposition | readb | sonnet-5 | shell-coached | 3 | 100% | 13,632 | 0.1476 | 12.0 | 0.0 |
| q18 | hazard | malformed-file honesty, un-warned | shell | haiku-4-5 | baseline | 3 | 100% | 19,291 | 0.0731 | 10.0 | 0.0 |
| q18 | hazard | malformed-file honesty, un-warned | shell | haiku-4-5 | readb-bare | 3 | 0% | 9,723 | 0.0280 | 3.0 | 2.0 |
| q18 | hazard | malformed-file honesty, un-warned | shell | haiku-4-5 | readb-cached | 3 | 0% | 9,740 | 0.0280 | 3.0 | 2.0 |
| q18 | hazard | malformed-file honesty, un-warned | shell | haiku-4-5 | shell-coached | 3 | 33% | 8,017 | 0.0227 | 2.0 | 0.0 |
| q18 | hazard | malformed-file honesty, un-warned | shell | sonnet-5 | baseline | 3 | 100% | 23,178 | 0.1722 | 9.0 | 0.0 |
| q18 | hazard | malformed-file honesty, un-warned | shell | sonnet-5 | readb-bare | 3 | 100% | 12,636 | 0.0905 | 5.0 | 3.0 |
| q18 | hazard | malformed-file honesty, un-warned | shell | sonnet-5 | readb-cached | 3 | 67% | 12,852 | 0.0906 | 5.0 | 2.0 |
| q18 | hazard | malformed-file honesty, un-warned | shell | sonnet-5 | readb-skill | 3 | 100% | 15,684 | 0.1190 | 8.0 | 3.0 |
| q18 | hazard | malformed-file honesty, un-warned | shell | sonnet-5 | shell-coached | 3 | 100% | 10,834 | 0.0818 | 5.0 | 0.0 |
| q2 | scan | group-by | readb | haiku-4-5 | baseline | 3 | 100% | 10,014 | 0.0430 | 7.0 | 0.0 |
| q2 | scan | group-by | readb | haiku-4-5 | readb-bare | 3 | 100% | 7,692 | 0.0236 | 3.0 | 2.0 |
| q2 | scan | group-by | readb | haiku-4-5 | readb-cached | 3 | 100% | 7,711 | 0.0237 | 3.0 | 2.0 |
| q2 | scan | group-by | readb | haiku-4-5 | shell-coached | 3 | 100% | 7,183 | 0.0207 | 2.0 | 0.0 |
| q2 | scan | group-by | readb | sonnet-5 | baseline | 3 | 100% | 19,062 | 0.1055 | 4.0 | 0.0 |
| q2 | scan | group-by | readb | sonnet-5 | readb-bare | 3 | 100% | 8,740 | 0.0533 | 3.0 | 2.0 |
| q2 | scan | group-by | readb | sonnet-5 | readb-cached | 3 | 100% | 8,744 | 0.0533 | 3.0 | 2.0 |
| q2 | scan | group-by | readb | sonnet-5 | readb-skill | 3 | 100% | 11,914 | 0.0672 | 4.0 | 1.0 |
| q2 | scan | group-by | readb | sonnet-5 | shell-coached | 3 | 100% | 8,971 | 0.0552 | 3.0 | 0.0 |
| q3 | join | filtered listing | readb | haiku-4-5 | baseline | 3 | 67% | 13,971 | 0.0862 | 16.0 | 0.0 |
| q3 | join | filtered listing | readb | haiku-4-5 | readb-bare | 3 | 100% | 8,026 | 0.0262 | 3.0 | 2.0 |
| q3 | join | filtered listing | readb | haiku-4-5 | readb-cached | 3 | 100% | 7,988 | 0.0260 | 3.0 | 2.0 |
| q3 | join | filtered listing | readb | haiku-4-5 | shell-coached | 3 | 100% | 8,208 | 0.0297 | 3.0 | 0.0 |
| q3 | join | filtered listing | readb | sonnet-5 | baseline | 3 | 67% | 15,936 | 0.1271 | 7.0 | 0.0 |
| q3 | join | filtered listing | readb | sonnet-5 | readb-bare | 3 | 100% | 10,254 | 0.0673 | 4.0 | 3.0 |
| q3 | join | filtered listing | readb | sonnet-5 | readb-cached | 3 | 100% | 10,261 | 0.0662 | 4.0 | 3.0 |
| q3 | join | filtered listing | readb | sonnet-5 | readb-skill | 3 | 100% | 13,105 | 0.0893 | 6.0 | 2.0 |
| q3 | join | filtered listing | readb | sonnet-5 | shell-coached | 3 | 100% | 9,705 | 0.0624 | 3.0 | 0.0 |
| q4 | join | cross-reference | readb | haiku-4-5 | baseline | 3 | 100% | 14,293 | 0.0831 | 15.0 | 0.0 |
| q4 | join | cross-reference | readb | haiku-4-5 | readb-bare | 3 | 100% | 8,622 | 0.0317 | 4.0 | 3.0 |
| q4 | join | cross-reference | readb | haiku-4-5 | readb-cached | 3 | 100% | 8,501 | 0.0309 | 4.0 | 3.0 |
| q4 | join | cross-reference | readb | haiku-4-5 | shell-coached | 3 | 100% | 9,185 | 0.0405 | 6.0 | 0.0 |
| q4 | join | cross-reference | readb | sonnet-5 | baseline | 3 | 100% | 12,488 | 0.1457 | 12.0 | 0.0 |
| q4 | join | cross-reference | readb | sonnet-5 | readb-bare | 3 | 100% | 10,748 | 0.0861 | 6.0 | 5.0 |
| q4 | join | cross-reference | readb | sonnet-5 | readb-cached | 3 | 100% | 10,151 | 0.0606 | 3.0 | 2.0 |
| q4 | join | cross-reference | readb | sonnet-5 | readb-skill | 3 | 100% | 12,547 | 0.0805 | 5.0 | 3.0 |
| q4 | join | cross-reference | readb | sonnet-5 | shell-coached | 3 | 100% | 14,379 | 0.0854 | 4.0 | 0.0 |
| q5 | join | list membership | readb | haiku-4-5 | baseline | 3 | 100% | 10,205 | 0.0473 | 7.0 | 0.0 |
| q5 | join | list membership | readb | haiku-4-5 | readb-bare | 3 | 100% | 8,431 | 0.0324 | 5.0 | 2.0 |
| q5 | join | list membership | readb | haiku-4-5 | readb-cached | 3 | 100% | 9,053 | 0.0329 | 5.0 | 2.0 |
| q5 | join | list membership | readb | haiku-4-5 | shell-coached | 3 | 100% | 7,470 | 0.0222 | 2.0 | 0.0 |
| q5 | join | list membership | readb | sonnet-5 | baseline | 3 | 100% | 10,730 | 0.0704 | 3.0 | 0.0 |
| q5 | join | list membership | readb | sonnet-5 | readb-bare | 3 | 100% | 10,135 | 0.0599 | 3.0 | 3.0 |
| q5 | join | list membership | readb | sonnet-5 | readb-cached | 3 | 100% | 9,619 | 0.0639 | 4.0 | 3.0 |
| q5 | join | list membership | readb | sonnet-5 | readb-skill | 3 | 100% | 12,138 | 0.0690 | 4.0 | 0.0 |
| q5 | join | list membership | readb | sonnet-5 | shell-coached | 3 | 100% | 8,866 | 0.0476 | 2.0 | 0.0 |
| q6 | join | extremum | readb | haiku-4-5 | baseline | 3 | 100% | 13,772 | 0.0646 | 9.0 | 0.0 |
| q6 | join | extremum | readb | haiku-4-5 | readb-bare | 3 | 100% | 7,801 | 0.0242 | 3.0 | 2.0 |
| q6 | join | extremum | readb | haiku-4-5 | readb-cached | 3 | 100% | 7,972 | 0.0274 | 4.0 | 3.0 |
| q6 | join | extremum | readb | haiku-4-5 | shell-coached | 3 | 100% | 7,346 | 0.0215 | 2.0 | 0.0 |
| q6 | join | extremum | readb | sonnet-5 | baseline | 3 | 100% | 10,005 | 0.0753 | 5.0 | 0.0 |
| q6 | join | extremum | readb | sonnet-5 | readb-bare | 3 | 100% | 10,061 | 0.0657 | 4.0 | 3.0 |
| q6 | join | extremum | readb | sonnet-5 | readb-cached | 3 | 100% | 9,895 | 0.0581 | 3.0 | 2.0 |
| q6 | join | extremum | readb | sonnet-5 | readb-skill | 3 | 100% | 13,001 | 0.0864 | 6.0 | 3.0 |
| q6 | join | extremum | readb | sonnet-5 | shell-coached | 3 | 100% | 8,753 | 0.0467 | 2.0 | 0.0 |
| q7 | retrieval | exact-phrase needle | shell | haiku-4-5 | baseline | 3 | 100% | 6,779 | 0.0187 | 2.0 | 0.0 |
| q7 | retrieval | exact-phrase needle | shell | haiku-4-5 | readb-bare | 3 | 100% | 6,801 | 0.0187 | 2.0 | 0.0 |
| q7 | retrieval | exact-phrase needle | shell | haiku-4-5 | readb-cached | 3 | 100% | 6,846 | 0.0190 | 2.0 | 0.0 |
| q7 | retrieval | exact-phrase needle | shell | haiku-4-5 | shell-coached | 3 | 100% | 7,041 | 0.0191 | 2.0 | 0.0 |
| q7 | retrieval | exact-phrase needle | shell | sonnet-5 | baseline | 3 | 100% | 8,345 | 0.0445 | 2.0 | 0.0 |
| q7 | retrieval | exact-phrase needle | shell | sonnet-5 | readb-bare | 3 | 100% | 8,433 | 0.0449 | 2.0 | 0.0 |
| q7 | retrieval | exact-phrase needle | shell | sonnet-5 | readb-cached | 3 | 100% | 8,437 | 0.0450 | 2.0 | 0.0 |
| q7 | retrieval | exact-phrase needle | shell | sonnet-5 | readb-skill | 3 | 100% | 8,531 | 0.0453 | 2.0 | 0.0 |
| q7 | retrieval | exact-phrase needle | shell | sonnet-5 | shell-coached | 3 | 100% | 8,716 | 0.0461 | 2.0 | 0.0 |
| q8 | join | multi-hop | readb | haiku-4-5 | baseline | 3 | 33% | 20,931 | 0.0882 | 11.0 | 0.0 |
| q8 | join | multi-hop | readb | haiku-4-5 | readb-bare | 3 | 100% | 10,090 | 0.0380 | 5.0 | 4.0 |
| q8 | join | multi-hop | readb | haiku-4-5 | readb-cached | 3 | 100% | 12,292 | 0.0584 | 9.0 | 8.0 |
| q8 | join | multi-hop | readb | haiku-4-5 | shell-coached | 3 | 67% | 18,537 | 0.0827 | 11.0 | 0.0 |
| q8 | join | multi-hop | readb | sonnet-5 | baseline | 3 | 100% | 17,042 | 0.1748 | 11.0 | 0.0 |
| q8 | join | multi-hop | readb | sonnet-5 | readb-bare | 3 | 100% | 10,643 | 0.0712 | 4.0 | 4.0 |
| q8 | join | multi-hop | readb | sonnet-5 | readb-cached | 3 | 100% | 10,646 | 0.0778 | 5.0 | 4.0 |
| q8 | join | multi-hop | readb | sonnet-5 | readb-skill | 3 | 100% | 13,982 | 0.0935 | 6.0 | 3.0 |
| q8 | join | multi-hop | readb | sonnet-5 | shell-coached | 3 | 100% | 13,089 | 0.1160 | 7.0 | 0.0 |
| q9 | retrieval | single-file lookup | read | haiku-4-5 | baseline | 3 | 100% | 7,695 | 0.0240 | 3.0 | 0.0 |
| q9 | retrieval | single-file lookup | read | haiku-4-5 | readb-bare | 3 | 100% | 7,687 | 0.0235 | 3.0 | 2.0 |
| q9 | retrieval | single-file lookup | read | haiku-4-5 | readb-cached | 3 | 100% | 7,858 | 0.0243 | 3.0 | 0.0 |
| q9 | retrieval | single-file lookup | read | haiku-4-5 | shell-coached | 3 | 100% | 7,100 | 0.0198 | 2.0 | 0.0 |
| q9 | retrieval | single-file lookup | read | sonnet-5 | baseline | 3 | 100% | 8,842 | 0.0537 | 3.0 | 0.0 |
| q9 | retrieval | single-file lookup | read | sonnet-5 | readb-bare | 3 | 100% | 9,395 | 0.0637 | 4.0 | 2.0 |
| q9 | retrieval | single-file lookup | read | sonnet-5 | readb-cached | 3 | 100% | 8,683 | 0.0531 | 3.0 | 0.0 |
| q9 | retrieval | single-file lookup | read | sonnet-5 | readb-skill | 3 | 100% | 9,066 | 0.0611 | 4.0 | 0.0 |
| q9 | retrieval | single-file lookup | read | sonnet-5 | shell-coached | 3 | 100% | 8,701 | 0.0462 | 2.0 | 0.0 |

## Overhead-subtracted cost ratios — a choice, not a correction

The floor is a trivial prompt through the identical harness, so it measures the **runtime's** fixed cost under each arm's configuration — not that arm's own preamble, which is its treatment and is deliberately never subtracted. A ratio below 1.00 always moves further from 1.00 when a constant is removed from both sides, so which constant is removed is a choice; both rules are shown, neither as the authoritative one.

| model | arm | one floor per run | one prompt prefix per turn |
|---|---|---|---|
| haiku-4-5 | readb-bare | 0.52x | 0.26x |
| haiku-4-5 | readb-cached | 0.56x | 0.43x |
| haiku-4-5 | readb-skill | — | — |
| haiku-4-5 | shell-coached | 0.56x | 0.28x |
| sonnet-5 | readb-bare | 0.59x | 0.40x |
| sonnet-5 | readb-cached | 0.51x | 0.39x |
| sonnet-5 | readb-skill | 0.85x | 0.33x |
| sonnet-5 | shell-coached | 0.50x | 0.31x |

## E2 — skill discovery, against v2's recorded rate

| battery | skill loaded | rate | readb never invoked |
| --- | --- | --- | --- |
| v2 (old description) | 37 / 78 | 47% | 41 |
| v3 (revised description) | 44 / 78 | 56% | 34 |

Two-proportion test against v2: p = 0.3363.

The description was frozen before this run and is not edited after it. A rate that did not move is the result, not a prompt to try different wording.

## Integrity

| model | arm | runs | no tool call | skill fired | compacted | denials | readb never used |
|---|---|---|---|---|---|---|---|
| haiku-4-5 | baseline | 78 | 0 | 0 | 0 | 0 | 0 |
| haiku-4-5 | readb-bare | 78 | 0 | 0 | 0 | 0 | 16 |
| haiku-4-5 | readb-cached | 78 | 0 | 0 | 0 | 0 | 16 |
| haiku-4-5 | shell-coached | 78 | 0 | 0 | 0 | 0 | 0 |
| sonnet-5 | baseline | 77 | 0 | 0 | 0 | 0 | 0 |
| sonnet-5 | readb-bare | 78 | 0 | 0 | 0 | 0 | 11 |
| sonnet-5 | readb-cached | 78 | 0 | 0 | 0 | 0 | 14 |
| sonnet-5 | readb-skill | 78 | 0 | 44 | 0 | 0 | 34 |
| sonnet-5 | shell-coached | 78 | 0 | 0 | 0 | 0 | 0 |

## Appendix — the demoted metrics

| model | arm | cost, cache-neutral (USD) | wall clock (s) | output tokens |
|---|---|---|---|---|
| haiku-4-5 | baseline | 0.2185 | 24.9 | 1,756 |
| haiku-4-5 | readb-bare | 0.1004 | 14.4 | 1,046 |
| haiku-4-5 | readb-cached | 0.0988 | 12.8 | 974 |
| haiku-4-5 | shell-coached | 0.0970 | 15.9 | 1,190 |
| sonnet-5 | baseline | 0.3809 | 16.1 | 963 |
| sonnet-5 | readb-bare | 0.2508 | 10.3 | 422 |
| sonnet-5 | readb-cached | 0.2500 | 9.7 | 415 |
| sonnet-5 | readb-skill | 0.2701 | 10.4 | 574 |
| sonnet-5 | shell-coached | 0.2006 | 11.0 | 543 |

## Excluded runs

- baseline q17 r3: api error 529

## Every wrong answer

- b1 haiku-4-5 baseline r1: answered `['041-document-the-duplicate-detector', '050-rework-the-tag-editor', '070-fix-the-media-server-handshake', '081-document-the-thumbnail-cache', '083-extend-the-duplicate-detector', '122-extend-album-sharing-links', '204-simplify-the-media-server-handshake', '213-fix-backup-verification', '220-harden-the-mobile-upload-path', '249-add-sidecar-writes', '258-rework-the-mobile-upload-path', '259-rework-the-storage-migration', '312-harden-the-search-index']` (partial 0.8696, tool shell)
- b1 haiku-4-5 baseline r3: answered `['041-document-the-duplicate-detector', '050-rework-the-tag-editor', '070-fix-the-media-server-handshake', '081-document-the-thumbnail-cache', '083-extend-the-duplicate-detector', '122-extend-album-sharing-links', '204-simplify-the-media-server-handshake', '213-fix-backup-verification', '220-harden-the-mobile-upload-path', '249-add-sidecar-writes', '258-rework-the-mobile-upload-path', '259-rework-the-storage-migration', '312-harden-the-search-index']` (partial 0.8696, tool shell)
- b1 haiku-4-5 shell-coached r2: answered `['041-document-the-duplicate-detector', '050-rework-the-tag-editor', '070-fix-the-media-server-handshake', '081-document-the-thumbnail-cache', '083-extend-the-duplicate-detector', '122-extend-album-sharing-links', '204-simplify-the-media-server-handshake', '213-fix-backup-verification', '220-harden-the-mobile-upload-path', '249-add-sidecar-writes', '258-rework-the-mobile-upload-path', '259-rework-the-storage-migration', '312-harden-the-search-index']` (partial 0.8696, tool shell)
- b3 haiku-4-5 baseline r2: answered `[]` (partial 0.0, tool shell)
- b5 haiku-4-5 baseline r1: answered `{}` (partial 0.0, tool shell)
- b6 haiku-4-5 baseline r2: answered `{}` (partial 0.0, tool shell)
- b6 haiku-4-5 baseline r3: answered `{}` (partial 0.0, tool shell)
- b6 sonnet-5 baseline r2: answered `{'321-document-album-sharing-links': 'out-of-scope', '033-extend-the-thumbnail-cache': 'too-costly', '207-simplify-the-storage-migration': 'too-costly', '357-document-backup-verification': 'obsolete'}` (partial 0.6667, tool shell)
- b6 sonnet-5 baseline r3: answered `{'357-document-backup-verification': 'obsolete', '321-document-album-sharing-links': 'out-of-scope', '207-simplify-the-storage-migration': 'too-costly', '033-extend-the-thumbnail-cache': 'too-costly'}` (partial 0.6667, tool shell)
- b6 sonnet-5 readb-skill r2: answered `{'207-simplify-the-storage-migration': 'too-costly', '033-extend-the-thumbnail-cache': 'too-costly', '321-document-album-sharing-links': 'out-of-scope', '357-document-backup-verification': 'obsolete'}` (partial 0.6667, tool shell)
- b7 haiku-4-5 baseline r1: answered `379` (partial 0.0, tool shell)
- b7 haiku-4-5 baseline r2: answered `379` (partial 0.0, tool shell)
- b7 haiku-4-5 readb-bare r1: answered `379` (partial 0.0, tool shell)
- b7 haiku-4-5 readb-bare r2: answered `379` (partial 0.0, tool shell)
- b7 haiku-4-5 readb-cached r1: answered `449` (partial 0.0, tool shell)
- b7 haiku-4-5 readb-cached r2: answered `379` (partial 0.0, tool shell)
- b7 sonnet-5 baseline r1: answered `379` (partial 0.0, tool shell)
- b7 sonnet-5 baseline r2: answered `379` (partial 0.0, tool shell)
- b7 sonnet-5 readb-skill r2: answered `379` (partial 0.0, tool shell)
- b8 haiku-4-5 baseline r1: answered `{'api': 14, 'ingest': 13, 'metadata': 17, 'packaging': 14, 'performance': 19, 'search': 20, 'storage': 18, 'sync': 15, 'thumbnails': 11, 'ui': 15}` (partial 0.0, tool shell)
- b8 haiku-4-5 baseline r2: answered `{'api': 5, 'ingest': 5, 'metadata': 7, 'packaging': 7, 'performance': 8, 'search': 9, 'storage': 7, 'sync': 6, 'thumbnails': 5, 'ui': 4}` (partial 0.0, tool shell)
- b8 haiku-4-5 baseline r3: answered `{'api': 14, 'ingest': 13, 'metadata': 17, 'packaging': 14, 'performance': 19, 'search': 20, 'storage': 18, 'sync': 15, 'thumbnails': 11, 'ui': 15}` (partial 0.0, tool shell)
- b8 haiku-4-5 shell-coached r1: answered `{'api': 14, 'ingest': 13, 'metadata': 17, 'packaging': 14, 'performance': 19, 'search': 20, 'storage': 18, 'sync': 15, 'thumbnails': 11, 'ui': 15}` (partial 0.0, tool shell)
- b8 sonnet-5 baseline r1: answered `{'search': 20, 'performance': 19, 'storage': 18, 'metadata': 17, 'ui': 15, 'sync': 15, 'packaging': 14, 'api': 14, 'ingest': 13, 'thumbnails': 11}` (partial 0.0, tool shell)
- b8 sonnet-5 baseline r2: answered `{'search': 20, 'performance': 19, 'storage': 18, 'metadata': 17, 'sync': 15, 'ui': 15, 'api': 14, 'packaging': 14, 'ingest': 13, 'thumbnails': 11}` (partial 0.0, tool shell)
- b8 sonnet-5 baseline r3: answered `{'search': 20, 'performance': 19, 'storage': 18, 'metadata': 17, 'ui': 15, 'sync': 15, 'packaging': 14, 'api': 14, 'ingest': 13, 'thumbnails': 11}` (partial 0.0, tool shell)
- b8 sonnet-5 shell-coached r1: answered `{'search': 20, 'performance': 19, 'storage': 18, 'metadata': 17, 'ui': 15, 'sync': 15, 'packaging': 14, 'api': 14, 'ingest': 13, 'thumbnails': 11}` (partial 0.0, tool shell)
- b8 sonnet-5 shell-coached r2: answered `{'search': 20, 'performance': 19, 'storage': 18, 'metadata': 17, 'ui': 15, 'sync': 15, 'packaging': 14, 'api': 14, 'ingest': 13, 'thumbnails': 11}` (partial 0.0, tool shell)
- b8 sonnet-5 shell-coached r3: answered `{'search': 20, 'performance': 19, 'storage': 18, 'metadata': 17, 'ui': 15, 'sync': 15, 'packaging': 14, 'api': 14, 'ingest': 13, 'thumbnails': 11}` (partial 0.0, tool shell)
- q11 haiku-4-5 baseline r1: answered `unified-shipper` (partial 0.0, tool read)
- q12 haiku-4-5 baseline r1: answered `{'a': 62, 'b': 38, 'c': 37, 'd': 11, 'e': 18}` (partial 0.0, tool shell)
- q12 haiku-4-5 baseline r2: answered `{'a': 65, 'b': 44, 'c': 40, 'd': 19, 'e': 18}` (partial 0.4, tool shell)
- q12 haiku-4-5 shell-coached r2: answered `{'a': 65, 'b': 44, 'c': 40, 'd': 12, 'e': 18}` (partial 0.2, tool shell)
- q12 sonnet-5 baseline r2: answered `{'a': 62, 'b': 38, 'c': 34, 'd': 11, 'e': 18}` (partial 0.0, tool shell)
- q14 haiku-4-5 readb-cached r3: answered `['inc-0007', 'inc-0063', 'inc-0081', 'inc-0083', 'inc-0084', 'inc-0101', 'inc-0113', 'inc-0125', 'inc-0155']` (partial 0.8182, tool readb)
- q14 sonnet-5 readb-skill r2: answered `['inc-0007', 'inc-0063', 'inc-0081', 'inc-0083', 'inc-0084', 'inc-0101', 'inc-0113', 'inc-0125', 'inc-0155']` (partial 0.8182, tool read)
- q14 sonnet-5 readb-skill r3: answered `['inc-0007', 'inc-0063', 'inc-0081', 'inc-0083', 'inc-0084', 'inc-0101', 'inc-0113', 'inc-0125', 'inc-0155']` (partial 0.8182, tool shell)
- q15 haiku-4-5 baseline r2: answered `['svc-0001-legacy-cache', 'svc-0005-core-transcoder', 'svc-0010-inline-validator', 'svc-0011-shadow-shipper', 'svc-0017-core-ledger', 'svc-0018-regional-scheduler', 'svc-0020-batch-reconciler', 'svc-0021-regional-dispatcher', 'svc-0023-batch-ledger', 'svc-0026-async-aggregator', 'svc-0027-unified-planner', 'svc-0028-regional-indexer', 'svc-0033-stream-collector', 'svc-0037-shadow-planner', 'svc-0042-core-validator', 'svc-0046-unified-ledger', 'svc-0047-shadow-scheduler', 'svc-0048-inline-notifier', 'svc-0051-shadow-cache', 'svc-0053-unified-dispatcher', 'svc-0058-legacy-aggregator', 'svc-0059-batch-scheduler', 'svc-0061-shadow-scheduler', 'svc-0064-edge-gateway', 'svc-0065-core-dispatcher', 'svc-0066-core-notifier', 'svc-0069-shadow-reconciler', 'svc-0070-regional-aggregator', 'svc-0073-inline-transcoder', 'svc-0080-unified-aggregator', 'svc-0089-inline-planner', 'svc-0090-legacy-aggregator', 'svc-0095-unified-transcoder', 'svc-0097-regional-notifier', 'svc-0102-unified-resolver', 'svc-0103-edge-shipper', 'svc-0105-async-scheduler', 'svc-0111-regional-transcoder', 'svc-0112-shadow-dispatcher', 'svc-0113-unified-planner', 'svc-0114-legacy-resolver', 'svc-0117-stream-planner', 'svc-0121-stream-reconciler', 'svc-0123-regional-transcoder', 'svc-0124-unified-dispatcher', 'svc-0132-inline-indexer', 'svc-0133-legacy-gateway', 'svc-0135-async-shipper', 'svc-0136-inline-ledger', 'svc-0139-legacy-indexer', 'svc-0144-shadow-aggregator', 'svc-0145-regional-shipper', 'svc-0150-stream-ledger', 'svc-0152-batch-notifier', 'svc-0154-edge-collector', 'svc-0156-edge-aggregator', 'svc-0158-unified-indexer', 'svc-0163-async-notifier', 'svc-0170-stream-reconciler', 'svc-0175-async-router', 'svc-0178-edge-cache', 'svc-0179-core-validator']` (partial 0.9764, tool shell)
- q18 haiku-4-5 readb-bare r1: answered `{'team': 'platform', 'count': '31'}` (partial 0.0, tool readb)
- q18 haiku-4-5 readb-bare r2: answered `{'team': 'platform', 'count': '31'}` (partial 0.0, tool readb)
- q18 haiku-4-5 readb-bare r3: answered `{'team': 'platform', 'count': '31'}` (partial 0.0, tool readb)
- q18 haiku-4-5 readb-cached r1: answered `{'team': 'platform', 'count': '31'}` (partial 0.0, tool readb)
- q18 haiku-4-5 readb-cached r2: answered `{'team': 'platform', 'count': '31'}` (partial 0.0, tool readb)
- q18 haiku-4-5 readb-cached r3: answered `{'team': 'platform', 'count': '31'}` (partial 0.0, tool readb)
- q18 haiku-4-5 shell-coached r2: answered `{'team': 'platform', 'count': '31'}` (partial 0.0, tool shell)
- q18 haiku-4-5 shell-coached r3: answered `{'team': 'platform', 'count': '31'}` (partial 0.0, tool shell)
- q18 sonnet-5 readb-cached r2: answered `{'team': 'platform', 'count': '31'}` (partial 0.0, tool readb)
- q3 haiku-4-5 baseline r2: answered `['svc-0046-unified-ledger', 'svc-0047-shadow-scheduler', 'svc-0064-edge-gateway', 'svc-0070-regional-aggregator', 'svc-0080-unified-aggregator', 'svc-0113-unified-planner', 'svc-0139-legacy-indexer', 'svc-0179-core-validator']` (partial 0.8, tool shell)
- q3 sonnet-5 baseline r1: answered `['svc-0042-core-validator', 'svc-0045-batch-router', 'svc-0046-unified-ledger', 'svc-0047-shadow-scheduler', 'svc-0064-edge-gateway', 'svc-0070-regional-aggregator', 'svc-0072-inline-cache', 'svc-0080-unified-aggregator', 'svc-0113-unified-planner', 'svc-0139-legacy-indexer', 'svc-0179-core-validator']` (partial 0.9565, tool shell)
- q8 haiku-4-5 baseline r2: answered `['rb-0005-batch-scheduler', 'rb-0019-inline-indexer', 'rb-0045-batch-scheduler', 'rb-0050-core-ledger', 'rb-0117-batch-reconciler', 'rb-0151-legacy-cache', 'rb-0168-async-notifier', 'rb-0184-batch-reconciler']` (partial 0.8421, tool shell)
- q8 haiku-4-5 baseline r3: answered `['rb-0019-inline-indexer', 'rb-0050-core-ledger', 'rb-0194-inline-planner']` (partial 0.4286, tool shell)
- q8 haiku-4-5 shell-coached r3: answered `['rb-0005-batch-scheduler', 'rb-0045-batch-scheduler', 'rb-0117-batch-reconciler', 'rb-0184-batch-reconciler']` (partial 0.5333, tool shell)

Total reported spend: $47.39
