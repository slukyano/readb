---
type: Widget
title: Second widget
tags: solo
beta: only-in-widget-two
flexible:
- 5
- 6
spec:
  rows: 20
  cols: 8
mix: 42
tag: [1, 2, 3]
score: 2.5
---

The second Widget. Demonstrates, against the first widget:

- `tags` as a bare scalar (promoted to a singleton list)
- `flexible` as a list where the sibling is a scalar (column becomes a LIST)
- `spec` as a nested map with a consistent key set (column becomes a STRUCT)
- `mix` as an int where the sibling is a string (unmixable -> JSON column)
- `tag` as a list of ints where the sibling is the string "1, 2, 3" (-> LIST<JSON>)
- `score` as a float where the sibling is an int (-> DOUBLE)
- a disjoint extra key (`beta`)
