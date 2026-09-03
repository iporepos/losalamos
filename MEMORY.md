# Memory Log

- 2026-09-03 — new manage_vault.py tool: three-level vault→branch→project→documents navigation; config uses [[vaults]] array; add_new_project simplified to accept folder or config with 'folder' key (no branch picker); manage_documents simplified to accept project folder directly; manage_vault writes temp JSON to pass vault context to add_new_project; imports _home from manage_documents

- 2026-09-03 — manage_documents: _active_documents now accepts folder_remote_documents and checks both local and remote paths; _action_edit/_action_delete use pj._locate_document_source() instead of hardcoded folder_root; _add_asset_document routes TeX tree to remote when configured; sidecar note stays local

- 2026-09-03 — moved TestLatexCompileErrorReal from tests/unit/test_documents_tex.py to tests/bcmk/test_documents_tex.py as BCMKTestDocumentTeXLatex; gated with @unittest.skipUnless(RUN_BENCHMARKS); keeps unit suite fast by not invoking real latexmk/pdflatex

- 2026-09-03 — add_new_project: removed branch from required config keys; first screen is now an interactive branch picker (_pick_branch/_list_branches); user picks existing branch or creates new one with [+]; branch prefix computed from selection

- 2026-09-03 — five bug fixes: (1) alias removed from _SYSTEM_KEYS so it's written to project note; (2) contractor/client/sapiens fields wrapped in [[...]] wiki-links; (3) _pick_party() in add_new_project — asks O/H then handles sapiens same/different/skip; (4) _print_columns auto-detects columns (<20→1, <40→2, 40+→3); (5) admin/documents and budget/documents removed from SUBFOLDERS; PDFs for invoice/receipt now go to inputs/documents

- 2026-09-03 — remote folder branch mirroring: add_new_project now passes folder_base=vault + branch=branch_folder to new_project() so rel=branch/name; load_project gains optional vault param to detect branch and set p.branch; manage_documents passes vault to load_project; TestProjectBranch gains test_load_project_with_vault_sets_branch

- 2026-09-03 — nomenclature refactor: basefolder→vault, prefix→branch, collection→branch across project.py (self.branch, _SYSTEM_KEYS, new_project()), add_new_project.py (vault/branch/folder_system/separator params, _next_increment rewrite with re.sub), manage_documents.py (same); sources templates restructured to [folders.search]/[folders.remote]/[templates.documents]; TOML now preferred format in all docstring examples; NoneType guard added to parse_metadata calls in _next_asset_id/_get_assets/_next_transfer_id/get_transfers

- 2026-09-03 — three bug fixes: (1) _pick_item letter prompt now uses 0=skip so Q-starting items are reachable; 0=skip also replaces ENTER=skip at selection prompt; (2) sources.toml template had documents/data keys nested under [templates.documents] — moved before that section so _resolve_remote_folders picks them up; (3) improved missing-key error messages in add_new_project and manage_documents to show found keys

- 2026-09-02 — fix duplicate sources config: new_project() now pre-places sources file before p.setup() so _install_config_templates sees it and skips blank; rank changed to prefer TOML; _load_sources_config search order updated to toml→yaml→yml→json

- 2026-09-02 — Phase 8: added _transfer.md template (data/ warning issued); NoteTransfer(NoteBasic) in notes.py; _next_transfer_id()/add_transfer()/get_transfers() in project.py; transfer_type inflow→budget/inflows/ outflow→budget/outflows/; tests in test_notes.py (TestNoteTransfer) and test_project.py (TestAddTransfer, TestGetTransfers)

- 2026-09-02 — Phase 7: extracted DocumentTeX.clean() from to_pdf() if-cleanup block; same is_main guard/latexmkrc detection/chdir-finally pattern; to_pdf() calls self.clean() in place of inline block; tests in test_documents_tex.py (TestDocumentTeXClean)

- 2026-09-02 — Phase 6: added LatexCompileError(RuntimeError) with source/returncode/log_path attrs; to_pdf() wraps subprocess.run in try/except — CalledProcessError→LatexCompileError with log_path if .log exists, FileNotFoundError→LatexCompileError("latexmk not found"); cleanup block gated on successful compile with explicit comment; tests in test_documents_tex.py

- 2026-09-02 — Phase 5: added FigureSVG._temp_working_copy() contextmanager (contextlib+tempfile.TemporaryDirectory); refactored to_image/to_pdf/to_svg to use it; crop_id temp_svg now lives in same temp dir (no separate make_local_tempfile call); make_local_tempfile untouched in utils.py; tests in test_figures.py

- 2026-09-02 — Phase 4: added Document.apply_config() no-op; Invoice._build_services_tex() static method generates LaTeX table from services list + tax_rate; Invoice/Receipt.apply_config() rewrites partials/services-invoice/receipt.tex; config=None param threaded through _add_asset_document/add_invoice/add_receipt; tests in test_documents.py

- 2026-09-02 — Phase 3: added folder_remote_documents/folder_remote_data (resolved via _resolve_remote_folders after _load_sources_config); _setup_remote_folders creates inputs/documents and inputs/data in remote roots; _locate_document_source now checks remote fallback; sources templates updated with documents/data keys
- 2026-09-02 — Phase 2: added collection attribute to Project (default None); folder_root = folder_base/collection/name when set, flat otherwise; main_note_path derived from folder_root; collection in _SYSTEM_KEYS (not written to note); load_project unaffected
- 2026-09-02 — Phase 1: unified document source to inputs/documents/{name}/; note at inputs/documents/{name}.md (local/Obsidian-visible); PDF shipped to type-specific target; added _locate_document_source(); removed subfolder param from _add_asset_document; add_receipt uses resolver for invoice lookup
- 2026-09-02 — Phase 0: added MbaE.load_config_file() static method (json/yaml/toml); updated boot() to branch on extension; replaced _load_files_overlay, _load_config, _load_sources_config inline blocks with calls to it; generalized FileSys.setup_subfolders(root, folder_list)

- 2026-08-31 — generalized tools prefix: renamed config key collection→prefix in add_new_project and manage_documents; removed .upper() coercion; fixed _next_increment to use case-insensitive matching; updated all docs/examples
- 2026-08-31 — CI fixes: added pyyaml to pyproject.toml dependencies; corrected test_tools_templates.py subprocess call from losalamos.tools.templates to losalamos.tools.update_templates
- 2026-08-31 — manage_documents: added delete action; removes TeX folder + PDFs but keeps sidecar note as tombstone; home listing filtered to active documents only via _active_documents(); _next_asset_id() naturally skips tombstone IDs
- 2026-08-31 — created tools/manage_documents.py: terminal document manager; project picker from collection, per-project home (add/edit/build); _load_projects reads titles without full project load; _open_in_explorer cross-platform; receipt links to invoice optionally
- 2026-08-31 — added Project.get_assets(): scans project tree for asset notes, returns DataFrame with asset_id/asset_type/name/asset_file sorted by asset_id
- 2026-08-31 — generalized build helper: _build_budget_document renamed to _build_asset_document(asset_type, file_id, subfolder); add_proposal()/build_proposal() added targeting admin/proposals/; all wrappers pass subfolder= explicitly
- 2026-08-31 — added language system: _DOC_TYPE_LABELS constant (en/pt-br); _localize_doc_type() reads language from main note; _patch_project_tex() sets DocVersion=001, DocFileID, DocType (localized) in definitions/project.tex after add_; tool config language key propagates to project note
- 2026-08-31 — DRY refactor of budget document system: _standard_files_overlay(), _add_budget_document(asset_type, files_overlay), _build_budget_document(asset_type, file_id); add/build invoice/receipt are now thin wrappers; build_receipt() added
- 2026-08-31 — asset naming convention: INVOICE/RECEIPT prefix first (INVOICE_C034_F003), version in PDF only (INVOICE_C034_F003_V003.pdf); build_invoice reads \DocVersion from definitions/project.tex, updates sidecar asset_file cref
- 2026-08-31 — added asset ID system: NoteAsset class in notes.py (_asset.md template); Project._next_asset_id() globs project tree for asset notes; add_invoice() now names folder+sidecar as INVOICE_{project}_{F00N} and creates NoteAsset sidecar in budget/documents/
- 2026-08-31 — created `src/losalamos/tools/add_new_project.py`: CLI wizard for creating numbered projects inside collection folders; reads tool config (basefolder/collection/sources), interactive pickers with alpha nav for org/sapiens/service, skip-all and q-to-quit keys, calls losalamos.new_project()
- 2026-08-31 — new_project: renamed specs→config, accepts dict/yaml/toml/json file; creates main note with metadata from config; copies sources file; added _load_config() helper; updated tests
- 2026-08-31 — module documentation pass on project.py: revised module/class docstrings, added config-file examples, docstrings for get_title/subtitle/contractor/contractor_sapiens/client/get_attribute, sources cross-refs in load_contractor/client/service, expanded make_overlay_service examples
- 2026-08-31 — added `templates/config/project/` with sources.json/yaml/toml; install picks best format per stem (yaml > toml > json); `FOLDER_TEMPLATES_CONFIG_PROJECT` in paths.py; `Project.setup()` + `_install_config_templates()`
- 2026-08-31 — added `service.tex` overlay: `load_service`, `make_overlay_service`; `_load_sources_config` reads `admin/config/sources.*` on `update()`; `NoteBasic` imported; `service` attrs in `__init__`; `_update_overlays` covers service
- 2026-08-31 — added `make_overlay_party_b_contractor/client`, `_build_party_b_placeholders`, `load_client`, `get_client`; initialized contractor_sapiens and client attrs in __init__
- 2026-08-31 — added `Project.make_overlay_file()`: reads a template (absolute or relative to data/templates), replaces placeholders, writes to admin/config/overlays/
- 2026-08-31 — extended `files_overlay` in `Document.new()` to also accept a path to a .json/.yaml/.toml config file; parsed via `_load_files_overlay` module-level helper; YAML needs pyyaml, TOML needs tomllib (3.11+) or tomli
- 2026-08-31 — revised `TestProjectContractor` and docstrings after user refactored `load_contractor` to be parameterless (reads from `self.sources`); added `load_contractor_sapiens` docstring and tests
- 2026-08-31 — clean-code pass on `Project.load_contractor`: extracted `_collect_md_files` private method, added Sphinx docstring, removed redundant final `if` branch, improved variable names
- 2026-08-31 — guarded `load_main_note()` call in `Project.update()` with `main_note_path.exists()` to prevent FileNotFoundError when the project note hasn't been created yet
- 2026-08-31 — fixed `update_name` (search for `# ` instead of assuming index 0) and `update_thumbnail` (write inside loop, no more IndexError) in NoteBasic to support templates where the image embed precedes the H1; fixed test roundtrip assertions to handle quoted name field
- 2026-08-31 — added `TestNoteOrganization` and `TestNoteSapiens` to test_notes.py (load_new, note_type, metadata fields, save roundtrip, abstract pattern)
- 2026-08-31 — added `NoteOrganization` and `NoteSapiens` (NoteBasic subclasses) plus `NoteCollOrganization` and `NoteCollSapiens` to notes.py, matching `_organization.md` and `_sapiens.md` templates
- 2026-08-31 — added mini-notebook `.. dropdown:: Example` blocks to `archive`, module-level `publish`, `Project.add_document`, and `Project.publish`; renamed all dropdown titles from "Script example" to "Example"
- 2026-08-31 — module documentation session: project.py — fixed broken `:returns:` backticks in `new_project`/`load_project`, added missing docstrings to `update`, `load_main_note`, and four private helper methods, removed module-docstring fluff, corrected "function"→"method" in `publish` note
