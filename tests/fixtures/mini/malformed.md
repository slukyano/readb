---
type: Malformed
title: This file has broken YAML frontmatter
items: [1, 2, 3
oops: : :
---

The frontmatter above is not valid YAML (an unclosed flow sequence and a bad mapping). This
file MUST be skipped with a warning, and the rest of the bundle MUST still load.
