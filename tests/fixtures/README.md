# Test fixtures

## `mini/` (to author — offline, no network)

A tiny hand-authored OKF bundle exercising the nasty cases from the design brief. To be created
during the implementation/test phase. It must include:

- a type with spaces and symbols (e.g. `Big %// Table` -> `bigtable`)
- a type normalizing to a leading digit (e.g. `3D Model` -> `_3dmodel`)
- a type normalizing to empty (routes to `__UNKNOWNTYPE`)
- two distinct types that collide after normalization (one gets a `_2` suffix + warning)
- two docs of one type with disjoint extra keys (union-of-keys -> NULLs)
- a `tags` list AND a bare-scalar `tags` (singleton promotion)
- a key that is scalar in one doc and a list in another (-> LIST)
- a key with a nested map (-> STRUCT or JSON)
- a doc with no `type`, and a doc whose `type` is a number (-> `__UNKNOWNTYPE`)
- a broken cross-link
- a stray `index.md`
- one malformed-YAML file that must be skipped with a warning

## `upstream/` (gitignored — clone on demand)

Google's reference bundles, for conformant multi-type / cross-linked coverage:

```sh
git clone --depth 1 https://github.com/GoogleCloudPlatform/knowledge-catalog tests/fixtures/upstream
# bundles at: tests/fixtures/upstream/okf/bundles/{ga4,stackoverflow,crypto_bitcoin}
```

- Primary fixture: `okf/bundles/ga4` (17 files; datasets/tables/references types).
- Join-stress fixture: `okf/bundles/crypto_bitcoin` (cross-table FK relationships in prose).
