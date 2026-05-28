#!/usr/bin/env python3
"""
Database Manager
================

A standalone Python tool for creating and managing environmental science databases
in `GeoPackage <https://www.geopackage.org/>`_ (SQLite) format. Designed around two
primitive but scalable schemas for spatial and time series data.

Everything runs through a single file — ``database.py`` — driven by JSON specs.

.. code-block:: bash

    pip install geopandas fiona pandas


Usage
-----

.. code-block:: bash

    python database.py --command initialize --parameters path/to/specs.json
    python database.py --command append     --parameters path/to/specs.json
    python database.py --command update     --parameters path/to/specs.json

Add ``--verbose`` for debug-level logging.

The specs file orchestrates all parameters. Multiple commands can coexist in the
same file; only the one named by ``--command`` is executed. Each command holds a
list of procedures, allowing batches.


Schemas
-------

Two primitive schemas cover most environmental science use cases.

**In-situ measurements**

The canonical case: temperature, precipitation, river level — anything measured
continuously at fixed locations. Works for point geometries (stations, gauges) and
polygon geometries (census tracts, regular grids, catchments).

``sites`` is the core geospatial layer. Wide table.

.. list-table::
   :header-rows: 1
   :widths: 15 10 50

   * - field
     - type
     - notes
   * - ``id``
     - int PK
     - auto-generated
   * - ``code``
     - text
     - sourced from provider or created; must be unique; indexed
   * - ``name``
     - text
     - short label; sized for composite names
   * - ``source``
     - text
     - inline citation or URL
   * - ``category``
     - text
     - e.g. climate station, rain gauge
   * - ``abstract``
     - text
     - comments on unusual sites, etc
   * - ``geometry``
     - geometry
     - usually point or polygon

``code`` is the source of identity. Duplicates not allowed on update.

``measurements`` is the core data. Long table. Non-spatial.

.. list-table::
   :header-rows: 1
   :widths: 15 10 50

   * - field
     - type
     - notes
   * - ``id``
     - int PK
     - auto-generated
   * - ``site_id``
     - int FK
     - → sites
   * - ``attribute_id``
     - int FK
     - → attributes
   * - ``datetime``
     - text
     - ``YYYY-MM-DD HH:MM:SS`` or ``YYYY-MM-DD``
   * - ``tier``
     - int
     - data level flag → tier table; DEFAULT 0
   * - ``quality``
     - int
     - quality flag → quality table; DEFAULT 0
   * - ``value``
     - real
     -

Each ``site_id–attribute_id–datetime–tier–quality`` combination is unique and indexed.
Default assimilation skips existing records (``append``); overwrite is explicit (``update``).

The ``time`` key in specs controls datetime resolution. If absent or null, defaults to
``true`` (full datetime). Set to ``false`` for date-only storage.

``attributes`` — semantic metadata for each measured variable.

.. list-table::
   :header-rows: 1
   :widths: 15 10 50

   * - field
     - type
     - notes
   * - ``code``
     - text
     - unique identifier
   * - ``alias``
     - text
     - short label
   * - ``name``
     - text
     - full name
   * - ``symbol``
     - text
     - LaTeX symbol
   * - ``units``
     - text
     - LaTeX units
   * - ``abstract``
     - text
     -
   * - ``subset``
     - text
     - math domain: ``real``, ``positive real``, ``probability``, etc
   * - ``domain_min`` / ``domain_max``
     - real
     - valid range
   * - ``category``
     - text
     - system classification: flow, level, ratio, etc
   * - ``theme``
     - text
     - thematic field: e.g. *Hydrology > Hillslope > Isotopes*

``tier`` and ``quality`` — small lookup tables for documenting flags.

.. list-table::
   :header-rows: 1
   :widths: 15 15

   * - field
     - type
   * - ``value``
     - int (unique)
   * - ``name``
     - text
   * - ``alias``
     - text
   * - ``symbol``
     - text
   * - ``abstract``
     - text

``storage`` — optional compression metadata per attribute.

.. list-table::
   :header-rows: 1
   :widths: 15 10 50

   * - field
     - type
     - notes
   * - ``attribute_id``
     - int FK
     - → attributes
   * - ``dtype``
     - text
     - e.g. ``float32``, ``int8``
   * - ``scale``
     - real
     - default 1.0
   * - ``offset``
     - real
     - default 0.0

``actual_value = (stored_value × scale) + offset``

If the table is empty or an attribute has no entry, ``scale=1`` and ``offset=0`` are
assumed. This applies to both retrieval and assimilation.

**Off-site measurements**

For environmental quality assessments: samples collected in the field, analysed later
in the lab. Sites produce samples (a bottle, a soil core) at a given datetime. Samples
produce measurements at a (possibly different) analysis datetime.

Multiple measurements can come from one sample — e.g. three replicate analyses entering
as ``tier=0`` (raw), their average entering as ``tier=1`` (consisted).

The quality flag handles detection limits (value receives the limit, quality maps to
"less than") and super-large values (value as power of 10, quality encodes the exponent).

``samples`` — field collection catalog. Wide table.

.. list-table::
   :header-rows: 1
   :widths: 15 10 50

   * - field
     - type
     - notes
   * - ``id``
     - int PK
     -
   * - ``code``
     - text
     -
   * - ``site_id``
     - int FK
     - → sites
   * - ``datetime``
     - text
     - sampling datetime
   * - ``abstract``
     - text
     - field comments

Identity is ``code–site_id–datetime``. Multiple samples at the same site and date are
allowed if they have different codes.

``measurements`` — same structure as in-situ, but ``site_id`` becomes ``sample_id``
(FK → samples).


Commands
--------

**initialize**

Creates a new GeoPackage database and loads seed data. Fails if the database already
exists.

.. code-block:: bash

    python database.py --command initialize --parameters specs.json

.. code-block:: json

    "initialize": [
      {
        "database": "path/to/output.gpkg",
        "category": "in-situ",
        "time": true,
        "sep": ";",

        "tables": {
          "sites":      {"file": "path/to/sites.gpkg", "layer": "sites"},
          "tier":       "path/to/tier.csv",
          "quality":    {"file": "path/to/quality.csv", "sep": ",", "header_lines": 2},
          "attributes": {"file": "path/to/attributes.csv", "sep": "\t"},
          "storage":    null,

          "measurements": "path/to/seed_data.csv"
        },

        "extra_sql": ["path/to/extra_fields.sql"]
      }
    ]

- ``category``: ``"in-situ"`` or ``"off-site"``
- ``time``: ``true`` (default) → ``YYYY-MM-DD HH:MM:SS``; ``false`` → ``YYYY-MM-DD``
- ``storage: null`` → table is created empty; scale=1, offset=0 assumed everywhere
- ``measurements`` (and ``samples`` for off-site) at init time are optional
- ``extra_sql``: optional list of ``.sql`` files for extra columns or extra tables

**append**

Adds new rows to any table. Records that already exist (matching the identity index)
are silently skipped. Batching is allowed.

.. code-block:: bash

    python database.py --command append --parameters specs.json

.. code-block:: json

    "append": [
      {
        "database":     "path/to/output.gpkg",
        "table":        "measurements",
        "data_file":    "path/to/new_data.csv",
        "sep":          ";",
        "header_lines": 4
      }
    ]

**update**

Same as ``append``, but existing records that collide with incoming data are overwritten.
Records with no collision are left untouched. New records are inserted normally.

.. code-block:: bash

    python database.py --command update --parameters specs.json

.. code-block:: json

    "update": [
      {
        "database":  "path/to/output.gpkg",
        "table":     "attributes",
        "data_file": "path/to/revised_attributes.csv"
      }
    ]


CSV Loading
-----------

The default field separator is ``;``. Two optional keys control how each file is read.

.. list-table::
   :header-rows: 1
   :widths: 15 10 50

   * - key
     - type
     - description
   * - ``sep``
     - string
     - field separator: ``";"``, ``","``, ``"\t"``, ``"|"``, etc.
   * - ``header_lines``
     - int
     - number of preamble lines to skip before the header row

Options can be set at two levels, with the per-table value taking priority:

1. **Per-table** — inside the table spec dict in ``tables``
2. **Procedure-level** — at the top of the procedure dict, as a fallback for all CSV
   tables in that step

A plain string path (no dict) always inherits from the procedure level. If neither
level specifies a key, the built-in default applies (``sep=";"``, ``header_lines=0``).

**Missing columns.** Incoming data does not need to supply every column in the target
table. The assimilation engine handles absent columns as follows:

- **Identity columns with a schema default** (e.g. ``tier``, ``quality`` — both
  ``DEFAULT 0`` in the measurements table): padded with the schema default value.
- **Non-identity optional columns** (e.g. ``abstract``, ``symbol``, ``units``):
  padded with ``NULL``.
- **Identity columns with no default** (e.g. ``site_id``, ``attribute_id``,
  ``datetime``): missing → hard error.

Extra columns in the incoming file that have no matching column in the target table
are dropped with a warning.


Foreign Key Resolution
----------------------

Incoming CSV data carries human-readable codes, not internal integer IDs. The
assimilation engine resolves codes to IDs automatically before inserting.

For ``measurements`` (in-situ) the CSV uses a ``site`` or ``site_id`` column resolved
against ``sites.code``, and an ``attribute`` or ``attribute_id`` column resolved against
``attributes.code``. The engine tries several column name candidates in order:

    ``site_id``  →  ``site``  →  ``sites_code``  →  ``site_code``  →  ``code``

Unresolvable codes raise an error listing the offending values.


Identity
--------

Each table has a defined set of columns that jointly identify a unique record.

.. list-table::
   :header-rows: 1
   :widths: 20 50

   * - table
     - identity columns
   * - ``sites``
     - ``code``
   * - ``attributes``
     - ``code``
   * - ``tier``
     - ``value``
   * - ``quality``
     - ``value``
   * - ``storage``
     - ``attribute_id``
   * - ``samples``
     - ``code``, ``site_id``, ``datetime``
   * - ``measurements``
     - ``site_id`` (or ``sample_id``), ``attribute_id``, ``datetime``, ``tier``, ``quality``


Extensibility
-------------

**Extra columns** — write an ``.sql`` file with ``ALTER TABLE ... ADD COLUMN ...``
statements and list it under ``extra_sql`` in the initialize spec. Useful additions
include ``sites.area_km2`` for polygon-based grids or catchment areas.

**Extra tables** — same mechanism. A ``CREATE TABLE`` in the ``.sql`` file adds a new
table at initialization. Useful for ``site_attributes`` populated from spatial joins.

Both are per-database: different databases initialized from different specs can have
different extra columns and tables without touching the core schema.


Notes
-----

The ``sites`` table is created and owned by the GeoPackage driver (via geopandas/Fiona),
ensuring the file is readable by QGIS, GDAL, and any GeoPackage-compliant library.
All other tables are plain SQLite tables inside the same file.

SQLite stores ``TEXT`` and ``DATETIME`` identically at the storage level. Datetime
columns are declared ``TEXT`` and formatted as ISO 8601 (``YYYY-MM-DD HH:MM:SS``),
which guarantees correct lexicographic ordering and compatibility with SQLite's
built-in date/time functions (``strftime``, ``date``, ``between``, etc.).

The tool uses ``PRAGMA foreign_keys = ON`` and ``PRAGMA journal_mode = WAL``.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Literal

import geopandas as gpd
import pandas as pd

log = logging.getLogger("losalamos")

# =============================================================================
# SQL SCHEMAS  (hard-coded, written to temp files on demand, deleted after use)
# =============================================================================

# Shared auxiliary tables — same for every schema category
_SQL_SHARED = """
CREATE TABLE IF NOT EXISTS tier (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    value    INTEGER NOT NULL UNIQUE,
    name     TEXT    NOT NULL,
    alias    TEXT,
    symbol   TEXT,
    abstract TEXT
);

CREATE TABLE IF NOT EXISTS quality (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    value    INTEGER NOT NULL UNIQUE,
    name     TEXT    NOT NULL,
    alias    TEXT,
    symbol   TEXT,
    abstract TEXT
);

CREATE TABLE IF NOT EXISTS attributes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    code       TEXT NOT NULL UNIQUE,
    alias      TEXT,
    name       TEXT,
    symbol     TEXT,
    units      TEXT,
    abstract   TEXT,
    subset     TEXT,
    domain_min REAL,
    domain_max REAL,
    category   TEXT,
    theme      TEXT
);

CREATE TABLE IF NOT EXISTS storage (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    attribute_id INTEGER NOT NULL UNIQUE REFERENCES attributes(id),
    dtype        TEXT,
    scale        REAL NOT NULL DEFAULT 1.0,
    offset       REAL NOT NULL DEFAULT 0.0
);
"""

# In-situ: measurements linked to sites
_SQL_INSITU_MEASUREMENTS = """
CREATE TABLE IF NOT EXISTS measurements (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id      INTEGER NOT NULL REFERENCES sites(fid),
    attribute_id INTEGER NOT NULL REFERENCES attributes(id),
    datetime     TEXT    NOT NULL,
    tier         INTEGER NOT NULL DEFAULT 0,
    quality      INTEGER NOT NULL DEFAULT 0,
    value        REAL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_measurements_identity
    ON measurements (site_id, attribute_id, datetime, tier, quality);
"""

# Off-site: samples linked to sites, measurements linked to samples
_SQL_OFFSITE_SAMPLES_MEASUREMENTS = """
CREATE TABLE IF NOT EXISTS samples (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    code     TEXT    NOT NULL,
    site_id  INTEGER NOT NULL REFERENCES sites(fid),
    datetime TEXT    NOT NULL,
    abstract TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_samples_identity
    ON samples (code, site_id, datetime);

CREATE TABLE IF NOT EXISTS measurements (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id    INTEGER NOT NULL REFERENCES samples(id),
    attribute_id INTEGER NOT NULL REFERENCES attributes(id),
    datetime     TEXT    NOT NULL,
    tier         INTEGER NOT NULL DEFAULT 0,
    quality      INTEGER NOT NULL DEFAULT 0,
    value        REAL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_measurements_identity
    ON measurements (sample_id, attribute_id, datetime, tier, quality);
"""

# GeoPackage bootstrap metadata tables (minimal spec-compliant)
_SQL_GPKG_BOOTSTRAP = """
PRAGMA application_id = 1196444487;
PRAGMA user_version   = 10300;

CREATE TABLE IF NOT EXISTS gpkg_spatial_ref_sys (
    srs_name                 TEXT    NOT NULL,
    srs_id                   INTEGER NOT NULL PRIMARY KEY,
    organization             TEXT    NOT NULL,
    organization_coordsys_id INTEGER NOT NULL,
    definition               TEXT    NOT NULL,
    description              TEXT
);

CREATE TABLE IF NOT EXISTS gpkg_contents (
    table_name  TEXT     NOT NULL PRIMARY KEY,
    data_type   TEXT     NOT NULL,
    identifier  TEXT,
    description TEXT     DEFAULT '',
    last_change DATETIME DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    min_x       REAL,
    min_y       REAL,
    max_x       REAL,
    max_y       REAL,
    srs_id      INTEGER  REFERENCES gpkg_spatial_ref_sys(srs_id)
);

CREATE TABLE IF NOT EXISTS gpkg_geometry_columns (
    table_name         TEXT NOT NULL,
    column_name        TEXT NOT NULL,
    geometry_type_name TEXT NOT NULL,
    srs_id             INTEGER NOT NULL REFERENCES gpkg_spatial_ref_sys(srs_id),
    z                  INTEGER NOT NULL DEFAULT 0,
    m                  INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT pk_geom_cols PRIMARY KEY (table_name, column_name)
);

INSERT OR IGNORE INTO gpkg_spatial_ref_sys VALUES
    ('Undefined Cartesian',   -1,   'NONE', -1, 'undefined', 'undefined Cartesian'),
    ('Undefined Geographic',   0,   'NONE',  0, 'undefined', 'undefined geographic'),
    ('WGS 84 Geographic 2D', 4326, 'EPSG', 4326,
     'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]',
     'WGS 84')
"""

# =============================================================================
# SCHEMA REGISTRY
# Each category entry defines:
#   sql_blocks      : list of SQL strings to execute after Fiona writes the spatial layer
#   spatial_tables  : {table_name: {"crs": ...}} — written via geopandas/Fiona
#   aux_tables      : tables loaded from CSV (in order)
#   table_identity  : {table: [cols]} — uniqueness definition per table
#   fk_resolution   : {table: {fk_col: {lookup_table, lookup_col}}}
# =============================================================================

SCHEMAS: dict[str, dict] = {
    "in-situ": {
        "sql_blocks": [_SQL_SHARED, _SQL_INSITU_MEASUREMENTS],
        "spatial_tables": {
            "sites": {"crs": "EPSG:4326"},
        },
        "aux_tables": ["tier", "quality", "attributes", "storage"],
        "table_identity": {
            "tier": ["value"],
            "quality": ["value"],
            "attributes": ["code"],
            "storage": ["attribute_id"],
            "measurements": ["site_id", "attribute_id", "datetime", "tier", "quality"],
        },
        "fk_resolution": {
            "measurements": {
                "site_id": {"lookup_table": "sites", "lookup_col": "code"},
                "attribute_id": {"lookup_table": "attributes", "lookup_col": "code"},
            },
        },
    },
    "off-site": {
        "sql_blocks": [_SQL_SHARED, _SQL_OFFSITE_SAMPLES_MEASUREMENTS],
        "spatial_tables": {
            "sites": {"crs": "EPSG:4326"},
        },
        "aux_tables": ["tier", "quality", "attributes", "storage"],
        "table_identity": {
            "tier": ["value"],
            "quality": ["value"],
            "attributes": ["code"],
            "storage": ["attribute_id"],
            "samples": ["code", "site_id", "datetime"],
            "measurements": [
                "sample_id",
                "attribute_id",
                "datetime",
                "tier",
                "quality",
            ],
        },
        "fk_resolution": {
            "samples": {
                "site_id": {"lookup_table": "sites", "lookup_col": "code"},
            },
            "measurements": {
                "sample_id": {"lookup_table": "samples", "lookup_col": "code"},
                "attribute_id": {"lookup_table": "attributes", "lookup_col": "code"},
            },
        },
    },
}


def get_schema(category: str) -> dict:
    key = category.lower().strip()
    if key not in SCHEMAS:
        valid = ", ".join(f"'{k}'" for k in SCHEMAS)
        raise ValueError(f"Unknown category '{category}'. Valid options: {valid}")
    return SCHEMAS[key]


# =============================================================================
# GEOPACKAGE / SQLITE UTILITIES
# =============================================================================


def gpkg_connect(path: Path) -> sqlite3.Connection:
    """Open (or create) a GeoPackage file. Bootstraps metadata if new."""
    is_new = not path.exists()
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")
    con.execute("PRAGMA journal_mode = WAL;")
    if is_new:
        gpkg_bootstrap(con)
    return con


def gpkg_bootstrap(con: sqlite3.Connection) -> None:
    """Write minimal GeoPackage metadata tables into a fresh database."""
    for stmt in _SQL_GPKG_BOOTSTRAP.split(";"):
        s = stmt.strip()
        if s:
            con.execute(s)
    con.commit()


def gpkg_exec_sql(con: sqlite3.Connection, sql: str) -> None:
    """
    Execute a block of SQL statements against con.
    Writes to a temp file in the module folder, executes, deletes.
    The file stays on disk if execution crashes — useful for debugging.
    """
    tmp_path = Path(__file__).parent / f"_tmp_{os.getpid()}.sql"
    try:
        tmp_path.write_text(sql, encoding="utf-8")
        clean_lines = [
            line for line in sql.splitlines() if not line.strip().startswith("--")
        ]
        cleaned = "\n".join(clean_lines)
        for stmt in cleaned.split(";"):
            s = stmt.strip()
            if s:
                con.execute(s)
        con.commit()
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def gpkg_exec_file(con: sqlite3.Connection, sql_path: Path) -> None:
    """Execute an external SQL file (for extra_sql extensions)."""
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")
    gpkg_exec_sql(con, sql_path.read_text(encoding="utf-8"))
    log.debug("Executed SQL file: %s", sql_path)


def gpkg_write_spatial(
    gdf: gpd.GeoDataFrame,
    gpkg_path: Path,
    layer: str,
    crs: str = "EPSG:4326",
) -> None:
    """Write a GeoDataFrame as a GeoPackage spatial layer via geopandas/Fiona."""
    if gdf.crs is None:
        log.warning("GeoDataFrame has no CRS — assuming %s", crs)
        gdf = gdf.set_crs(crs)
    elif str(gdf.crs) != crs:
        log.info("Reprojecting from %s to %s", gdf.crs, crs)
        gdf = gdf.to_crs(crs)
    gdf.to_file(str(gpkg_path), layer=layer, driver="GPKG", mode="w")
    log.info("Spatial layer '%s' → %s (%d features)", layer, gpkg_path.name, len(gdf))


def gpkg_table_exists(con: sqlite3.Connection, table: str) -> bool:
    row = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def gpkg_table_columns(con: sqlite3.Connection, table: str) -> list[str]:
    rows = con.execute(f"PRAGMA table_info({table})").fetchall()
    return [row[1] for row in rows]


def gpkg_table_info(con: sqlite3.Connection, table: str) -> dict[str, dict]:
    """
    Return column metadata keyed by column name.
    Each value is a dict with keys: type, notnull, dflt_value.
    """
    rows = con.execute(f"PRAGMA table_info({table})").fetchall()
    return {
        row[1]: {"type": row[2], "notnull": bool(row[3]), "dflt_value": row[4]}
        for row in rows
    }


def gpkg_pk_col(con: sqlite3.Connection, table: str) -> str:
    """Return the primary key column name — 'fid' for Fiona tables, 'id' otherwise."""
    cols = gpkg_table_columns(con, table)
    return "fid" if "fid" in cols else "id"


def gpkg_code_id_map(
    con: sqlite3.Connection, table: str, code_col: str = "code"
) -> dict[str, int]:
    """Return {code: pk_id} for any table with a code column."""
    pk = gpkg_pk_col(con, table)
    rows = con.execute(f"SELECT {code_col}, {pk} FROM {table}").fetchall()
    return {row[0]: row[1] for row in rows}


def detect_category(con: sqlite3.Connection) -> str:
    """Heuristic: off-site if 'samples' table exists, else in-situ."""
    return "off-site" if gpkg_table_exists(con, "samples") else "in-situ"


def detect_has_time(con: sqlite3.Connection) -> bool:
    """Infer datetime resolution from an existing measurements row."""
    try:
        row = con.execute("SELECT datetime FROM measurements LIMIT 1").fetchone()
        if row and row[0]:
            return ":" in str(row[0])
    except Exception:
        pass
    return True  # default


# =============================================================================
# DATA LOADING & FK RESOLUTION
# =============================================================================


def load_csv(path: str | Path, sep: str = ";", skiprows: int = 0) -> pd.DataFrame:
    """
    Load a delimited text file into a DataFrame.

    Parameters
    ----------
    sep      : field separator (default ";")
    skiprows : number of preamble lines to skip before the header row
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Data file not found: {p}")
    df = pd.read_csv(p, dtype=str, sep=sep, skiprows=skiprows)
    df.columns = [c.strip().lower() for c in df.columns]
    log.debug(
        "Loaded %d rows from %s  (sep=%r  skiprows=%d)", len(df), p, sep, skiprows
    )
    return df


def _read_opts(proc: dict, table_spec: Any = None) -> dict:
    """
    Resolve CSV read options with a two-level fallback:

        per-table spec  →  procedure-level  →  built-in defaults

    table_spec is the raw value from specs["tables"][table_name].
    It may be a plain string path, or a dict carrying "file" plus optional
    "sep" and "header_lines" keys alongside any other table-specific keys.

    Absent or null values at every level are ignored so defaults apply silently.
    """
    opts: dict[str, Any] = {}

    # proc-level fallback (applies to all tables in this procedure unless overridden)
    if proc.get("sep") is not None:
        opts["sep"] = proc["sep"]
    if proc.get("header_lines") is not None:
        opts["skiprows"] = int(proc["header_lines"])

    # per-table override (only available when table_spec is a dict)
    if isinstance(table_spec, dict):
        if table_spec.get("sep") is not None:
            opts["sep"] = table_spec["sep"]
        if table_spec.get("header_lines") is not None:
            opts["skiprows"] = int(table_spec["header_lines"])

    return opts


def _parse_csv_spec(spec: Any) -> tuple[str, dict]:
    """
    Parse a table spec from the 'tables' dict in an initialize procedure.

    Accepts two forms:
        "path/to/file.csv"
        {"file": "path/to/file.csv", "sep": ",", "header_lines": 3}

    Returns (file_path_str, raw_spec) so that _read_opts can inspect the dict.
    The raw spec is passed through unchanged; _read_opts handles key extraction.
    """
    if isinstance(spec, dict):
        if "file" not in spec:
            raise ValueError(f"Table spec dict is missing required 'file' key: {spec}")
        return spec["file"], spec
    return str(spec), {}


def _parse_spatial_spec(spec: Any) -> tuple[str, str | None]:
    """
    Parse a spatial table spec.  Accepts:
        {"file": "path/to/sites.gpkg", "layer": "sites"}
        "path/to/sites.gpkg"
    """
    if isinstance(spec, dict):
        if "file" not in spec:
            raise ValueError(
                f"Spatial spec dict is missing required 'file' key: {spec}"
            )
        return spec["file"], spec.get("layer")
    return str(spec), None


def load_spatial(path: str | Path, layer: str | None = None) -> gpd.GeoDataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Spatial file not found: {p}")
    kwargs: dict[str, Any] = {"filename": str(p)}
    if layer:
        kwargs["layer"] = layer
    gdf = gpd.read_file(**kwargs)
    gdf.columns = [c.strip().lower() for c in gdf.columns]
    log.debug("Loaded %d features from %s", len(gdf), p)
    return gdf


def resolve_fk(
    df: pd.DataFrame,
    con: sqlite3.Connection,
    fk_rules: dict[str, dict],
) -> pd.DataFrame:
    """
    Replace code-based columns with integer FK ids.

    Incoming CSV may use the FK column name (e.g. 'site_id') containing codes,
    OR alternative names like 'sites_code' or 'site_code'. All candidates are tried.
    """
    df = df.copy()
    for fk_col, rule in fk_rules.items():
        lookup_table = rule["lookup_table"]
        lookup_col = rule["lookup_col"]
        id_map = gpkg_code_id_map(con, lookup_table, code_col=lookup_col)
        source_col = _find_fk_source_col(df, fk_col, lookup_table, lookup_col)

        if source_col is None:
            raise ValueError(
                f"Cannot resolve FK '{fk_col}': no matching column found in data. "
                f"Tried: '{fk_col}', '{lookup_table}_code', "
                f"'{lookup_table.rstrip('s')}_code', '{lookup_col}'"
            )

        codes = df[source_col].astype(str)
        df[fk_col] = codes.map(id_map)

        missing_mask = df[fk_col].isna()
        if missing_mask.any():
            bad = codes[missing_mask].unique().tolist()
            raise ValueError(
                f"FK resolution for '{fk_col}': {len(bad)} code(s) not found "
                f"in '{lookup_table}.{lookup_col}': {bad[:10]}"
            )

        df[fk_col] = df[fk_col].astype(int)
        if source_col != fk_col and source_col in df.columns:
            df = df.drop(columns=[source_col])

    return df


def _find_fk_source_col(
    df: pd.DataFrame, fk_col: str, lookup_table: str, lookup_col: str
) -> str | None:
    # fk_col stripped of _id suffix  e.g. "site_id" -> "site", "attribute_id" -> "attribute"
    fk_bare = fk_col[:-3] if fk_col.endswith("_id") else fk_col
    candidates = [
        fk_col,  # site_id
        fk_bare,  # site
        f"{lookup_table}_{lookup_col}",  # sites_code
        f"{lookup_table.rstrip('s')}_code",  # site_code
        lookup_col,  # code
    ]
    for c in candidates:
        if c in df.columns:
            return c
    return None


def normalise_datetime(df: pd.DataFrame, has_time: bool) -> pd.DataFrame:
    if "datetime" not in df.columns:
        return df
    df = df.copy()
    fmt = "%Y-%m-%d %H:%M:%S" if has_time else "%Y-%m-%d"
    try:
        df["datetime"] = pd.to_datetime(df["datetime"]).dt.strftime(fmt)
    except Exception as exc:
        raise ValueError(f"Could not parse 'datetime' column: {exc}") from exc
    return df


def align_columns(
    df: pd.DataFrame,
    db_cols: list[str],
    identity_cols: list[str],
    col_info: dict[str, dict] | None = None,
) -> pd.DataFrame:
    """
    Align df to the target table's column set.

    - Columns in df that don't exist in the table are dropped (with a warning).
    - Missing identity columns are a hard error UNLESS the schema declares a
      DEFAULT value for that column — in which case they are padded with it.
      This covers tier/quality (DEFAULT 0) arriving without those columns.
    - Missing non-identity columns are padded with their schema DEFAULT if one
      exists, otherwise NULL. A debug message notes each padded column.
    - The auto-generated pk columns (id, fid) are always excluded from the result.

    col_info is the output of gpkg_table_info(). If None, missing columns are
    always padded with NULL (no default awareness).
    """
    target = [c for c in db_cols if c not in ("id", "fid")]

    # Extra columns in incoming data — drop with a warning
    extra = [c for c in df.columns if c not in db_cols]
    if extra:
        log.warning("Columns not in table schema — ignored: %s", extra)

    missing = [c for c in target if c not in df.columns]
    if missing:
        df = df.copy()
        for col in missing:
            default = (
                col_info[col]["dflt_value"] if col_info and col in col_info else None
            )

            if col in identity_cols and default is None:
                raise ValueError(
                    f"Identity column '{col}' is missing from incoming data "
                    "and has no schema default. This column is required."
                )

            fill = default  # may be None (→ NULL) or a string like '0'
            if fill is not None:
                log.debug(
                    "Column '%s' absent — filled with schema default: %s", col, fill
                )
            else:
                log.debug("Column '%s' absent — filled with NULL", col)
            df[col] = fill

    return df[target]


# =============================================================================
# CORE INSERT / UPSERT ENGINE
# =============================================================================

Mode = Literal["append", "update"]


def insert_rows(
    con: sqlite3.Connection,
    table: str,
    df: pd.DataFrame,
    identity_cols: list[str],
    mode: Mode = "append",
) -> dict[str, int]:
    """
    Insert df into table with duplicate handling.

    append : INSERT OR IGNORE  — duplicates skipped
    update : INSERT OR IGNORE + targeted UPDATE for collisions (never DELETEs rows, so FK children are safe)
    """
    if df.empty:
        log.info("No rows to insert into '%s'", table)
        return {"inserted": 0, "skipped": 0}

    db_cols = gpkg_table_columns(con, table)
    col_info = gpkg_table_info(con, table)
    df = align_columns(df, db_cols, identity_cols, col_info)
    cols = list(df.columns)
    rows = [tuple(r) for r in df.itertuples(index=False, name=None)]
    placeholders = ", ".join(["?"] * len(cols))
    insert_sql = (
        f"INSERT OR IGNORE INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
    )

    cursor = con.cursor()

    if mode == "append":
        cursor.executemany(insert_sql, rows)
        con.commit()
        inserted = max(cursor.rowcount, 0)
        skipped = len(rows) - inserted
        log.info(
            "Table '%s': %d rows → %d inserted, %d skipped",
            table,
            len(rows),
            inserted,
            skipped,
        )
        return {"inserted": inserted, "skipped": skipped}

    # mode == "update"
    update_cols = [c for c in cols if c not in identity_cols]
    col_idx = {c: i for i, c in enumerate(cols)}
    inserted = updated = 0

    if not identity_cols or not update_cols:
        # No safe upsert possible — use REPLACE (only for tables without FK children)
        replace_sql = f"INSERT OR REPLACE INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
        cursor.executemany(replace_sql, rows)
        con.commit()
        inserted = max(cursor.rowcount, 0)
    else:
        set_clause = ", ".join(f"{c}=?" for c in update_cols)
        where_clause = " AND ".join(f"{c}=?" for c in identity_cols)
        update_sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

        for row in rows:
            cursor.execute(insert_sql, row)
            if cursor.rowcount == 0:
                set_vals = tuple(row[col_idx[c]] for c in update_cols)
                where_vals = tuple(row[col_idx[c]] for c in identity_cols)
                cursor.execute(update_sql, set_vals + where_vals)
                updated += 1
            else:
                inserted += 1
        con.commit()

    log.info(
        "Table '%s': %d rows → %d inserted, %d updated",
        table,
        len(rows),
        inserted,
        updated,
    )
    return {"inserted": inserted, "updated": updated}


# =============================================================================
# COMMAND: initialize
# =============================================================================


def cmd_initialize(procedures: list[dict[str, Any]]) -> None:
    for i, proc in enumerate(procedures):
        log.info(
            "── initialize [%d/%d] ──────────────────────────────",
            i + 1,
            len(procedures),
        )
        _initialize_one(proc)


def _initialize_one(proc: dict[str, Any]) -> None:
    db_path = Path(_req(proc, "database"))
    category = _req(proc, "category")
    tables_spec = _req(proc, "tables")
    has_time = bool(proc.get("time", True))
    extra_sql = proc.get("extra_sql") or []

    schema = get_schema(category)

    if db_path.exists():
        raise FileExistsError(
            f"Database already exists: {db_path}. "
            "Delete it or use 'append'/'update' to add data."
        )
    db_path.parent.mkdir(parents=True, exist_ok=True)

    log.info("Creating: %s  [category=%s  time=%s]", db_path, category, has_time)

    # ── Step 1: write spatial tables via Fiona (creates the .gpkg file) ──────
    for table_name, spatial_cfg in schema["spatial_tables"].items():
        spec = tables_spec.get(table_name)
        if not spec:
            raise ValueError(
                f"Required spatial table '{table_name}' missing from spec 'tables'."
            )
        file_path, layer = _parse_spatial_spec(spec)
        gdf = load_spatial(file_path, layer=layer)
        gpkg_write_spatial(gdf, db_path, layer=table_name, crs=spatial_cfg["crs"])

    # ── Step 2: open connection, execute non-spatial DDL ─────────────────────
    con = gpkg_connect(db_path)
    try:
        for sql_block in schema["sql_blocks"]:
            gpkg_exec_sql(con, sql_block)

        for sql_path_str in extra_sql:
            gpkg_exec_file(con, Path(sql_path_str))

        # ── Step 3: load auxiliary tables ────────────────────────────────────
        for table_name in schema["aux_tables"]:
            raw_spec = tables_spec.get(table_name)
            if raw_spec is None:
                log.info("Table '%s': no source file — skipped (empty)", table_name)
                continue
            file_path, table_spec = _parse_csv_spec(raw_spec)
            df = load_csv(file_path, **_read_opts(proc, table_spec))
            fk_rules = schema["fk_resolution"].get(table_name, {})
            if fk_rules:
                df = resolve_fk(df, con, fk_rules)
            identity = schema["table_identity"].get(table_name, [])
            insert_rows(con, table_name, df, identity_cols=identity, mode="append")

        # ── Step 4: optional seed data for samples / measurements at init ─────
        for opt_table in ("samples", "measurements"):
            raw_spec = tables_spec.get(opt_table)
            if not raw_spec:
                continue
            log.info("Loading optional '%s' at init time", opt_table)
            file_path, table_spec = _parse_csv_spec(raw_spec)
            df = load_csv(file_path, **_read_opts(proc, table_spec))
            fk_rules = schema["fk_resolution"].get(opt_table, {})
            if fk_rules:
                df = resolve_fk(df, con, fk_rules)
            df = normalise_datetime(df, has_time)
            identity = schema["table_identity"].get(opt_table, [])
            insert_rows(con, opt_table, df, identity_cols=identity, mode="append")

    finally:
        con.close()

    log.info("Database ready: %s", db_path)


# =============================================================================
# COMMAND: append
# =============================================================================


def cmd_append(procedures: list[dict[str, Any]]) -> None:
    for i, proc in enumerate(procedures):
        log.info(
            "── append [%d/%d] ──────────────────────────────────",
            i + 1,
            len(procedures),
        )
        _assimilate_one(proc, mode="append")


# =============================================================================
# COMMAND: update
# =============================================================================


def cmd_update(procedures: list[dict[str, Any]]) -> None:
    for i, proc in enumerate(procedures):
        log.info(
            "── update [%d/%d] ──────────────────────────────────",
            i + 1,
            len(procedures),
        )
        _assimilate_one(proc, mode="update")


# =============================================================================
# SHARED ASSIMILATION (append + update)
# =============================================================================


def _assimilate_one(proc: dict[str, Any], mode: Mode) -> None:
    db_path = Path(_req(proc, "database"))
    table = _req(proc, "table")
    data_file = _req(proc, "data_file")

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    con = gpkg_connect(db_path)
    try:
        category = detect_category(con)
        schema = get_schema(category)
        has_time = detect_has_time(con)

        # For append/update the read opts live at the proc level only
        # (there is no per-table spec dict here — the file is named directly)
        df = load_csv(data_file, **_read_opts(proc))

        fk_rules = schema["fk_resolution"].get(table, {})
        if fk_rules:
            df = resolve_fk(df, con, fk_rules)

        if "datetime" in df.columns:
            df = normalise_datetime(df, has_time)

        identity = schema["table_identity"].get(table, [])
        insert_rows(con, table, df, identity_cols=identity, mode=mode)

    finally:
        con.close()


# =============================================================================
# HELPERS
# =============================================================================


def _req(d: dict, key: str) -> Any:
    val = d.get(key)
    if val is None:
        raise ValueError(f"Required key '{key}' missing from procedure spec.")
    return val


# =============================================================================
# DISPATCHER
# =============================================================================

COMMANDS = {
    "initialize": cmd_initialize,
    "append": cmd_append,
    "update": cmd_update,
}


def dispatch(command: str, specs: dict) -> None:
    handler = COMMANDS.get(command)
    if handler is None:
        raise ValueError(f"Unknown command '{command}'. Valid: {list(COMMANDS)}")

    procedures = specs.get(command)
    if not procedures:
        raise ValueError(
            f"Command '{command}' not found in specs (or list is empty). "
            f"Available keys: {list(specs.keys())}"
        )
    if not isinstance(procedures, list):
        raise TypeError(f"Specs key '{command}' must be a list of procedure dicts.")

    handler(procedures)


# =============================================================================
# CLI
# =============================================================================


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
        level=level,
        stream=sys.stdout,
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="database.py",
        description="losalamos — GeoPackage database manager",
    )
    parser.add_argument("--command", "-c", required=True, choices=list(COMMANDS))
    parser.add_argument("--parameters", "-p", required=True, metavar="SPECS_JSON")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)

    setup_logging(args.verbose)

    specs_path = Path(args.parameters)
    if not specs_path.exists():
        log.error("Specs file not found: %s", specs_path)
        return 1

    try:
        specs = json.loads(specs_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        log.error("Invalid JSON in specs file: %s", exc)
        return 1

    try:
        dispatch(args.command, specs)
        log.info("Done.")
        return 0
    except (FileNotFoundError, FileExistsError, ValueError, TypeError) as exc:
        log.error("%s", exc)
        return 1
    except Exception as exc:
        log.exception("Unexpected error: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
