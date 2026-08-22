# Benchmark results — v2

54 runs recorded, 0 excluded as invalid, 54 used.
Models: claude-sonnet-5. Arms: baseline, readb-bare, shell-coached. Questions: 3.

## Messy against tidy — the same questions, two renderings

| model | arm | question | messy cost | tidy cost | messy/tidy | exact m/t |
|---|---|---|---|---|---|---|
| sonnet-5 | baseline | q15 | 0.1250 | 0.1839 | 0.68x | 100%/100% |
| sonnet-5 | baseline | q2 | 0.0983 | 0.0931 | 1.06x | 100%/100% |
| sonnet-5 | baseline | q3 | 0.1216 | 0.1199 | 1.01x | 67%/100% |
| sonnet-5 | readb-bare | q15 | 0.0703 | 0.0694 | 1.01x | 100%/100% |
| sonnet-5 | readb-bare | q2 | 0.0655 | 0.0644 | 1.02x | 100%/100% |
| sonnet-5 | readb-bare | q3 | 0.0600 | 0.0603 | 0.99x | 100%/100% |
| sonnet-5 | shell-coached | q15 | 0.0712 | 0.0854 | 0.83x | 100%/100% |
| sonnet-5 | shell-coached | q2 | 0.0551 | 0.0544 | 1.01x | 100%/100% |
| sonnet-5 | shell-coached | q3 | 0.0705 | 0.0680 | 1.04x | 100%/100% |


Total reported spend: $4.74
