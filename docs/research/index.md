---
okf_version: "0.1"
---

# Research

An OKF bundle of durable research artifacts: one `type: Research` concept per study. Dated
point-in-time observations (adoption numbers, version checks) are kept *with* their dates.
Produced by research tasks in [`tasks/`](../../tasks/index.md); registered in the repo's
`.readb/config.toml`.

```sh
readb query "SELECT __name, surveyed, title FROM research" --bundle ./docs/research
```

* [Similar markdown+frontmatter tools](similar-tools.md) - 11 tools surveyed 2026-07-17; conventions, adoption, adopt/reject calls (sprint-002).
