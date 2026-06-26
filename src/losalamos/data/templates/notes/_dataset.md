---
note_type: dataset
timestamp: <% tp.file.creation_date("YYYY-MM-DD HH:mm:ss") %>
tags:
  - dataset-note
aliases:
subject:
category:
alias:
name:  <% tp.file.title %>
cite_inline:
cite_bibli:
entry_type: dataset
doi:
url:
author:
title:
year:
note:
organization:
abstract:
acquisition:
level: 
method:
source:
source_alias:
version:
license:
access:
format:
structure:
datetime_start:
datetime_end:
timestep:
extent:
bbox:
crs:
resolution:  
---
# <% tp.file.title %>

DATASET

![[<% tp.file.title %>.jpeg|200]]

**`=this.title`**

By `=this.cite_inline`

- URL: `=this.url`

> [!Info] Abstract
> {a paragraph description of the note}

---

# Overview

> [!Abstract]+ Highlights
> - List highlights

> [!Example]+ Related
> - List related notes

---
# Description

*Start typing here*

---
# Specifications

*Start typing here*

---
# Downloading

*Start typing here*

---
# Loading

*Start typing here*

---
# References

*Start typing here*

---
# Resources

*Start typing here*

# Attributes glossary

| Field | Description | Controlled vocabulary |
| :--- | :--- | :--- |
| `note_type` | Note type identifier | `"dataset"` |
| `tags` | Thematic domain tags | e.g. `hydrology`, `topography`, `climatology`, `land use`, `soil`, `bathymetry`, `vegetation`, `demography`, `infrastructure` |
| `category` | Dataset-type qualifier; theme-dependent | Elevation: `"DTM"` `"DSM"` `"DSM-V"` `"DSM-B"` `"DSM-VB"` |
| `alias` | Short informal name or acronym | free string |
| `cite_inline` | Formatted in-line citation | free string |
| `cite_bibli` | Formatted full bibliographic citation | free string |
| `entry_type` | BibTeX entry type | `"dataset"` |
| `doi` | Dataset DOI | free string |
| `url` | Distribution URL — where to access or download | free string |
| `author` | Author(s) or institution | free string |
| `title` | Full official title | free string |
| `year` | Publication or release year | free string |
| `note` | Informal notes, distribution channels, related links | free string |
| `organization` | Publishing organization | free string |
| `abstract` | Short description of dataset content and purpose | free string |
| `acquisition` | Local storage status | `"not acquired"` `"partial"` `"acquired"` |
| `level` | Acquisition intent | `"radar"` `"backbone"` |
| `method` | Observation or production method; implies reproducibility level | Irreproducible: `"in situ"` `"in vitro"` `"remote sensing"` `"reported"` — Reproducible: `"harmonized"` (compilation) `"derived"` (any analysis), `"reanalysis"` (simulation models) |
| `source` | Canonical source — institution or author who produced and owns the dataset, can include Obsidian citation brackets | `"[[United States Geological Survey]]"` |
| `source_alias` | Canonical source assigned short name | e.g. `USGS` |
| `version` | Dataset version or collection identifier | free string |
| `license` | Formal license instrument | e.g. `"CC-BY 4.0"` `"public domain"` `"proprietary"` |
| `access` | Practical retrieval method | `"open scriptable"` `"open api key"` `"open manual"` `"licensed"` `"restricted"` |
| `format` | Data format type | `"tabular"` `"vector"` `"raster"` |
| `structure` | Format subtype | tabular: `"generic"` `"time series"` `"sample event"` — vector: `"point"` `"line"` `"polygon"` `"mixed"` — raster: `"single band"` `"multi band"` `"time stack"` `"multi band time stack"` |
| `datetime_start` | Date field for Start of temporal coverage | e.g. `"2000-02-11"` |
| `datetime_end` | Date field for end of temporal coverage; `null` = still active | e.g. `"2019-02-01"` |
| `timestep` | Finest temporal resolution | e.g. `"daily"` `"16 days"` `"annual"` `"single epoch"` |
| `extent` | Human-readable spatial coverage; scope inferred from this. Actual boudary is also inferred or mapped via hash table. | e.g. `"Brazil"` `"Amazon River Basin"` `"Earth"` |
| `bbox` | Bounding box as WKT string for geodetic coordinates (typically WGS84). Can be computed programmatically later | e.g. `"POLYGON((-74 -34, -28 -34, -28 6, -74 6, -74 -34))"` |
| `crs` | Sourced Coordinate Reference System id (authority_code),  can include Obsidian citation brackets | e.g. `EPSG_4326`, `"[[EPSG_4326]]"` |
| `resolution` | Finest available spatial resolution — defines dataset identity. String number and units. Numeric value can be inferred programmatically downstream | e.g. `"30 m"` `"0.25 degrees"` `"500 m"` |

**Design notes**

- `datetime_end`: null → open, continuously updated; explicit past date → closed/frozen; `datetime_start == datetime_end` → single acquisition epoch
- `license` and `access` are distinct: license is the formal legal instrument, access is the practical retrieval method
- spatial attributes are kept empty if not applicable.

---
# Bibliographic information

## In-line citation
```
{cite_inline}
```

## Full citation
```
{cite_bibli}
```

## BibTeX entry
```
{bibtex}
```