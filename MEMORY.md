# Memory Log

- 2026-08-31 — revised `TestProjectContractor` and docstrings after user refactored `load_contractor` to be parameterless (reads from `self.sources`); added `load_contractor_sapiens` docstring and tests
- 2026-08-31 — clean-code pass on `Project.load_contractor`: extracted `_collect_md_files` private method, added Sphinx docstring, removed redundant final `if` branch, improved variable names
- 2026-08-31 — guarded `load_main_note()` call in `Project.update()` with `main_note_path.exists()` to prevent FileNotFoundError when the project note hasn't been created yet
- 2026-08-31 — fixed `update_name` (search for `# ` instead of assuming index 0) and `update_thumbnail` (write inside loop, no more IndexError) in NoteBasic to support templates where the image embed precedes the H1; fixed test roundtrip assertions to handle quoted name field
- 2026-08-31 — added `TestNoteOrganization` and `TestNoteSapiens` to test_notes.py (load_new, note_type, metadata fields, save roundtrip, abstract pattern)
- 2026-08-31 — added `NoteOrganization` and `NoteSapiens` (NoteBasic subclasses) plus `NoteCollOrganization` and `NoteCollSapiens` to notes.py, matching `_organization.md` and `_sapiens.md` templates
- 2026-08-31 — added mini-notebook `.. dropdown:: Example` blocks to `archive`, module-level `publish`, `Project.add_document`, and `Project.publish`; renamed all dropdown titles from "Script example" to "Example"
- 2026-08-31 — module documentation session: project.py — fixed broken `:returns:` backticks in `new_project`/`load_project`, added missing docstrings to `update`, `load_main_note`, and four private helper methods, removed module-docstring fluff, corrected "function"→"method" in `publish` note
