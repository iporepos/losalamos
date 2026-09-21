![Style Status](https://github.com/iporepos/losalamos/actions/workflows/style.yaml/badge.svg)
![Docs Status](https://github.com/iporepos/losalamos/actions/workflows/docs.yaml/badge.svg)
![Tests Status](https://github.com/iporepos/losalamos/actions/workflows/tests.yaml/badge.svg)
![Top Language](https://img.shields.io/github/languages/top/iporepos/losalamos)
![Status](https://img.shields.io/badge/status-development-yellow.svg)
[![Code Style](https://img.shields.io/badge/style-black-000000.svg)](https://github.com/psf/black)
[![Documentation](https://img.shields.io/badge/docs-online-blue)](https://iporepos.github.io/losalamos/)
[![PyPI Latest Release](https://img.shields.io/pypi/v/losalamos.svg?label=PyPI)](https://pypi.org/project/losalamos/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/losalamos.svg?label=PyPI%20downloads)](
https://pypi.org/project/losalamos/)


<a logo>
<img src="https://raw.githubusercontent.com/iporepos/losalamos/master/docs/figs/logo.png" height="130" width="130">
</a>

---

# Los Alamos

A Python toolkit for productivity and research. 

> [!NOTE]
> Check out the [documentation website](https://iporepos.github.io/losalamos/)

---

# Install easily

```bash
python -m pip install losalamos
```

---

# Quick Gallery

## Project

Create and manage structured project folders with metadata, financial tracking, and document generation.

```python
import losalamos

# create a project — builds folder structure and installs the Obsidian note
pj = losalamos.new_project(config={
    "folder_base": "/projects",
    "name": "Survey2026",
    "title": "Environmental Survey 2026",
    "status": "planning",
    "sources": "/vault/sources.toml",
})

# load an existing project
pj = losalamos.load_project(project_folder="/projects/Survey2026")

# query assets and financial transfers as DataFrames
assets    = pj.get_assets()
transfers = pj.get_transfers()

# issue an invoice and build its PDF
pj.add_invoice()
pj.build_invoice(file_id="INV-001")
```

---

## Notes

Structured Markdown notes backed by YAML frontmatter, Obsidian-ready templates, and typed collections.

```python
from losalamos.notes import NoteProject, NoteReference, NoteCollection

# load and inspect a project note
note = NoteProject()
note.load(file_note="Survey2026/Survey2026.md")
print(note.metadata["title"])

# create a reference note from BibTeX metadata
ref = NoteReference()
ref.load_new(
    file_note="smith2022.md",
    metadata={
        "entry_type": "article",
        "name":       "smith2022",
        "author":     "Smith, John and Doe, Jane",
        "title":      "River flow trends under climate change",
        "year":       "2022",
        "journal":    "Hydrology Journal",
    },
)
ref.save()

# scan a folder as a typed collection
coll = NoteCollection()
coll.load_folder("vault/notes/projects")
for n in coll:
    print(n.name, n.metadata.get("status"))
```

```python
# rename a note and propagate the link update across the vault
note = NoteProject()
note.load(file_note="old_name.md")
note.refactor(new_name="new_name", scope="vault/notes")
```

---

## Documents

Scaffold TeX documents from layered templates with optional private overlays.

```python
from losalamos.documents import Report

# create a report from the built-in template
report = Report(name="AnnualReport", alias="AR")
report.new(folder="/projects/Survey2026/outputs", name="annual_report")

# apply a client-specific overlay (logos, cover page, etc.)
report.new(
    folder="/projects/Survey2026/outputs",
    name="client_report",
    template_overlay="/private/client_x",
)
```

---

## Figures

Raster image utilities and Inkscape SVG manipulation with multi-format export.

```python
from losalamos.figures import Figure, FigureSVG

# generate a JPEG thumbnail from any raster image
Figure.make_thumbnail(
    file_input="photo.png",
    file_output="thumb.jpg",
    size=(512, 512),
    mode="crop",
)

# load an Inkscape SVG and export to PDF hiding selected layers
svg = FigureSVG()
svg.load_data(file_data="diagram.svg")
svg.to_pdf(file_output="diagram.pdf", hide_layers=["annotations"])

# or render a PNG with only specific layers visible
svg.to_image(file_output="figure.png", dpi=300, show_layers=["background", "data"])
```

---

## Ingestion

Automated PDF + BibTeX ingestion pipeline for managed reference libraries.

```python
from losalamos.ingestion import Ingester

# pair PDFs with their BibTeX files, normalize metadata,
# create reference notes, and copy PDFs into the library
ing = Ingester(src="incoming/papers", dst="library/papers")
ing.run()
```

