---
type: '%%%'
title: Type that normalizes to empty
description: All characters are deleted by normalization, so this routes to __UNKNOWNTYPE.
---

The `type` here is non-empty as a string but normalizes to the empty string, so this concept
is non-conformant and lands in `__UNKNOWNTYPE` (while still appearing in `__DOCUMENTS`).
