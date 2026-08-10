---
type: Task
title: The shipped skill's leading example assumes uv is installed
description: skills/readb/SKILL.md opens with `uvx readb …`, which fails on a machine where readb is installed but uv is not.
status: Draft
priority: medium
tags:
- skill
- docs
- agents
created: 2026-08-10
---

Found by the agent-efficiency benchmark (`024`, sprint-004), where it invalidated a whole arm
before it was understood. The benchmark gave the skill arm `readb` on `PATH` but not `uv`; 17 of
36 runs issued `uvx readb …`, got `exit 127: command not found`, and spent extra turns
recovering. The arm measured 1.21× the baseline's cost until the environment was corrected, at
which point it measured 1.01×.

The benchmark environment was artificial, but the assumption is not:

```
skills/readb/SKILL.md:14   uvx readb query "SELECT …" --bundle ./library
skills/readb/SKILL.md:15   uv tool install readb    # or install it once and drop the uvx prefix
```

The first runnable line an agent reads requires `uv`. Line 15 mentions the alternative, but an
agent that copies the leading example on a machine with `readb` on `PATH` and no `uv` gets a
failure it then has to diagnose. Machines where readb was installed by pip, pipx, Homebrew, a
distribution package, or a plain venv are exactly this case.

## Notes (to refine)

- The cheapest fix is ordering: lead with bare `readb …`, and mention `uvx readb` as the
  no-install path afterwards. That inverts the current presentation.
- Consider having the skill open with a one-line capability probe (`command -v readb || echo
  "use: uvx readb"`), so the agent resolves the invocation once instead of guessing.
- The same assumption may sit in `README.md` and the plugin manifest — check all three surfaces
  together, not just the skill.
- The skill is distributed pinned to a commit through the plugin marketplace, so a correction
  reaches installed copies only on re-pin; worth confirming how that interacts with
  [027-plugin-marketplace-submission](027-plugin-marketplace-submission.md).
