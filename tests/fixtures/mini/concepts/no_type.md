---
title: No type field at all
description: A doc missing the required `type` field. Permissive consumers must not crash.
tags:
- untyped
---

This concept has no `type` field, so it routes to `__UNKNOWNTYPE` (with a NULL type) and still
appears in `__DOCUMENTS`.
