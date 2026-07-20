"""Acceptance criteria 1-12 from the design brief (docs/design-brief.md).

Each test is annotated with the criterion number it covers. Criteria that exercise conformant
multi-type data run against the upstream ``ga4`` bundle (skipped if not cloned); the rest run
against the always-present offline ``mini`` bundle.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import readb
from readb.database import Database


def _md_files(bundle: Path) -> list[Path]:
    return sorted(bundle.rglob("*.md"))


def _concept_md_files(bundle: Path) -> list[Path]:
    """All .md files excluding the reserved index.md / log.md at any level."""
    return [p for p in _md_files(bundle) if p.name not in {"index.md", "log.md"}]


# --- Criterion 1: __DOCUMENTS row count for ga4 = .md files excluding index.md/log.md ---------


def test_documents_count_excludes_reserved_files(ga4_db: Database, ga4_path: Path) -> None:
    expected = len(_concept_md_files(ga4_path))
    actual = ga4_db.sql("SELECT count(*) AS n FROM __DOCUMENTS")[0]["n"]
    assert actual == expected == 11


# --- Criterion 2: each distinct type yields a table; schema lists names/columns/mapping --------


def test_each_type_yields_table_and_schema_lists_mapping(ga4_db: Database) -> None:
    schema = ga4_db.schema()
    # Every detected original type has a normalized table whose columns are reported.
    assert schema.type_mapping == {
        "bigquerydataset": "BigQuery Dataset",
        "bigquerytable": "BigQuery Table",
        "reference": "Reference",
    }
    for table_name, original in schema.type_mapping.items():
        assert table_name in schema.tables
        table = schema.tables[table_name]
        assert table.original_type == original
        assert table.columns  # columns + inferred types are present
        # The table actually exists and is queryable in DuckDB.
        ga4_db.sql(f'SELECT * FROM "{table_name}" LIMIT 1')


# --- Criterion 3: a missing optional key in one doc -> NULL, not an error (union-of-keys) ------


def test_union_of_keys_is_lossless_with_nulls(mini_db: Database) -> None:
    rows = {r["__path"]: r for r in mini_db.sql("SELECT __path, alpha, beta FROM widget")}
    one = rows["concepts/widget_one.md"]
    two = rows["concepts/widget_two.md"]
    # widget_one has `alpha` but not `beta`; widget_two is the mirror image.
    assert one["alpha"] == "only-in-widget-one"
    assert one["beta"] is None
    assert two["alpha"] is None
    assert two["beta"] == "only-in-widget-two"


# --- Criterion 4: __INDEXES has one row per index.md with the union of frontmatter fields ------


def test_indexes_table_one_row_per_index_file(ga4_db: Database, ga4_path: Path) -> None:
    expected = sum(1 for p in _md_files(ga4_path) if p.name == "index.md")
    actual = ga4_db.sql("SELECT count(*) AS n FROM __INDEXES")[0]["n"]
    assert actual == expected == 6


def test_indexes_union_of_frontmatter_and_log_present(mini_db: Database) -> None:
    # mini has one stray index.md (no frontmatter) and one log.md.
    index_rows = mini_db.sql("SELECT __path FROM __INDEXES")
    assert [r["__path"] for r in index_rows] == ["index.md"]
    # __LOG exists only because a log.md is present, and holds that one row.
    log_rows = mini_db.sql("SELECT __path FROM __LOG")
    assert [r["__path"] for r in log_rows] == ["log.md"]


# --- Criterion 5: no/non-string/empty-norm type -> __UNKNOWNTYPE AND still in __DOCUMENTS ------


def test_unknowntype_routing_and_documents_membership(mini_db: Database) -> None:
    unknown = {r["__path"] for r in mini_db.sql("SELECT __path FROM __UNKNOWNTYPE")}
    assert unknown == {
        "concepts/no_type.md",  # missing type
        "concepts/numeric_type.md",  # non-string type (int 42)
        "concepts/empty_type.md",  # type normalizes to empty
    }
    # All three also appear in __DOCUMENTS (with their raw/NULL type).
    docs = {r["__path"] for r in mini_db.sql("SELECT __path FROM __DOCUMENTS")}
    assert unknown <= docs


# --- Criterion 6: normalization rules + collision suffixing with a warning --------------------


def test_normalization_rules() -> None:
    from readb.schema import normalize_type

    assert normalize_type("Big %// Table") == "bigtable"
    assert normalize_type("3D Model") == "_3dmodel"
    assert normalize_type("%%%") == ""


def test_collision_gets_suffix_and_warning(mini_db: Database) -> None:
    schema = mini_db.schema()
    # The two distinct types "Big %// Table" and "bigtable" both normalize to "bigtable".
    assert {schema.type_mapping["bigtable"], schema.type_mapping["bigtable_2"]} == {
        "Big %// Table",
        "bigtable",
    }
    assert any("collision" in w for w in schema.warnings)
    # Leading-digit normalization produced a real table.
    assert schema.type_mapping["_3dmodel"] == "3D Model"


# --- Criterion 7: __path ends in .md and is bundle-relative; __body has body, no YAML ----------


def test_path_and_body_virtual_fields(mini_db: Database) -> None:
    row = mini_db.sql(
        "SELECT __path, __name, __body FROM widget WHERE __path = 'concepts/widget_one.md'"
    )[0]
    assert row["__path"] == "concepts/widget_one.md"
    assert row["__path"].endswith(".md")
    assert row["__name"] == "widget_one"  # simple file name: no directories, no .md
    assert "The first Widget" in row["__body"]
    assert "---" not in row["__body"]
    assert "type:" not in row["__body"]  # no frontmatter leaked into the body


# --- Criterion 8: tags is a LIST column; __TAGS view supports JOIN-based tag filtering ----------


def test_tags_is_list_with_singleton_promotion(mini_db: Database) -> None:
    assert mini_db.schema().tables["widget"].columns["tags"] == "VARCHAR[]"
    rows = {r["__path"]: r["tags"] for r in mini_db.sql("SELECT __path, tags FROM widget")}
    assert rows["concepts/widget_one.md"] == ["red", "blue"]
    assert rows["concepts/widget_two.md"] == ["solo"]  # bare scalar promoted to a singleton


def test_tags_view_supports_join_filtering(mini_db: Database) -> None:
    # Find documents tagged "example" by joining the normalized __TAGS view back to __DOCUMENTS.
    rows = mini_db.sql(
        """
        SELECT d.__path
        FROM __DOCUMENTS d
        JOIN __TAGS t ON d.__path = t.concept_path
        WHERE t.tag = 'example'
        """
    )
    assert [r["__path"] for r in rows] == ["concepts/broken_link.md"]


# --- Criterion 9: type unification (double / LIST / LIST<JSON> / JSON) -------------------------


def test_type_unification(mini_db: Database) -> None:
    cols = mini_db.schema().tables["widget"].columns
    assert cols["score"] == "DOUBLE"  # int mixed with float
    assert cols["flexible"] == "BIGINT[]"  # scalar in one doc, list in another -> LIST
    assert cols["tag"] == "JSON[]"  # "1, 2, 3" (str) vs [1,2,3] (ints) -> LIST<JSON>
    assert cols["mix"] == "JSON"  # str vs int -> unmixable -> JSON
    assert cols["spec"].startswith("STRUCT(")  # consistent nested map -> STRUCT


def test_json_fallback_preserves_values(mini_db: Database) -> None:
    import json

    rows = {r["__path"]: r for r in mini_db.sql("SELECT __path, mix, tag FROM widget")}
    # `mix` JSON column round-trips both the string and the int losslessly.
    assert json.loads(rows["concepts/widget_one.md"]["mix"]) == "hello"
    assert json.loads(rows["concepts/widget_two.md"]["mix"]) == 42
    # `tag` LIST<JSON>: the comma-string stays a string; the ints stay ints.
    assert [json.loads(x) for x in rows["concepts/widget_one.md"]["tag"]] == ["1, 2, 3"]
    assert [json.loads(x) for x in rows["concepts/widget_two.md"]["tag"]] == [1, 2, 3]


# --- Criterion 10: a cross-type JOIN on __path returns correct rows ----------------------------


def test_cross_type_join_on_path(ga4_db: Database) -> None:
    rows = ga4_db.sql(
        """
        SELECT d.__path, d.type, t.title
        FROM __DOCUMENTS d
        JOIN bigquerytable t ON d.__path = t.__path
        """
    )
    assert len(rows) == 1
    assert rows[0]["type"] == "BigQuery Table"
    assert rows[0]["__path"] == "tables/events_.md"


# --- Criterion 11: a malformed-YAML file is skipped with a warning; the load still succeeds -----


def test_malformed_file_skipped_but_load_succeeds(mini_db: Database, caplog) -> None:
    # malformed.md never becomes a row in any table.
    docs = {r["__path"] for r in mini_db.sql("SELECT __path FROM __DOCUMENTS")}
    assert "malformed.md" not in docs
    # And the rest of the bundle loaded fine.
    assert mini_db.sql("SELECT count(*) AS n FROM __DOCUMENTS")[0]["n"] == 9


def test_malformed_file_emits_warning(mini_path: Path, caplog) -> None:
    import logging

    with caplog.at_level(logging.WARNING, logger="readb.parser"):
        readb.open(str(mini_path)).close()
    assert any("malformed.md" in rec.getMessage() for rec in caplog.records)


def test_frontmatter_key_shadowing_virtual_column_warns_and_is_ignored(
    tmp_path: Path, caplog
) -> None:
    import logging

    (tmp_path / "x.md").write_text("---\ntype: T\n__raw: sneaky\n---\nbody\n", encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="readb.loader"):
        db = readb.open(str(tmp_path))
    try:
        row = db.sql("SELECT __raw FROM t")[0]
        assert row["__raw"].startswith("---")  # the injected file text, not the producer value
        assert any("shadows a virtual column" in rec.getMessage() for rec in caplog.records)
    finally:
        db.close()


def test_sql_table_carries_columns_on_empty_result(mini_db: Database) -> None:
    """``Database.sql_table`` returns column names even when the result has zero rows."""
    columns, rows = mini_db.sql_table("SELECT __name, __path FROM __DOCUMENTS WHERE false")
    assert columns == ["__name", "__path"]
    assert rows == []
    # And the dict-shaped sibling stays consistent with it on non-empty results.
    columns, rows = mini_db.sql_table("SELECT __path FROM __DOCUMENTS ORDER BY __path LIMIT 1")
    dicts = mini_db.sql("SELECT __path FROM __DOCUMENTS ORDER BY __path LIMIT 1")
    assert dicts == [dict(zip(columns, row, strict=True)) for row in rows]


def test_producer_name_key_is_inert_to_virtual_name(tmp_path: Path) -> None:
    """The name contract (sprint-002): ``__name`` is immutable and filename-derived; a producer
    ``name:`` frontmatter key becomes an ordinary column and never affects ``__name``."""
    (tmp_path / "actual-file.md").write_text(
        "---\ntype: T\nname: Pretty Display Name\n---\nbody\n", encoding="utf-8"
    )
    db = readb.open(str(tmp_path))
    try:
        row = db.sql("SELECT __name, name FROM t")[0]
        assert row["__name"] == "actual-file"
        assert row["name"] == "Pretty Display Name"
    finally:
        db.close()


# --- Criterion 12: no files are created or modified in the bundle during any operation ---------


def _hash_tree(bundle: Path) -> dict[str, str]:
    digests: dict[str, str] = {}
    for path in sorted(bundle.rglob("*")):
        if path.is_file():
            digests[str(path.relative_to(bundle))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


def test_no_files_created_or_modified(mini_path: Path) -> None:
    before = _hash_tree(mini_path)
    db = readb.open(str(mini_path))
    db.sql("SELECT * FROM __DOCUMENTS")
    db.sql("SELECT * FROM widget")
    db.sql("SELECT * FROM __TAGS")
    db.schema()
    db.close()
    after = _hash_tree(mini_path)
    assert before == after  # identical file set and identical contents
