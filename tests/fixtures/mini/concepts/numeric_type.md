---
type: 42
title: Type is a number, not a string
description: A non-string `type` is non-conformant and routes to __UNKNOWNTYPE.
---

YAML parses this `type` as the integer 42. Because it is not a string, the concept routes to
`__UNKNOWNTYPE` and still appears in `__DOCUMENTS` with its raw (numeric) type.
