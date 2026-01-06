![Top Language](https://img.shields.io/github/languages/top/iporepos/copyme)
![Status](https://img.shields.io/badge/status-development-yellow.svg)
[![Code Style](https://img.shields.io/badge/style-black-000000.svg)](https://github.com/psf/black)
[![Documentation](https://img.shields.io/badge/docs-online-blue)](https://iporepos.github.io/copyme/)
![Style Status](https://github.com/iporepos/copyme/actions/workflows/style.yaml/badge.svg)
![Docs Status](https://github.com/iporepos/copyme/actions/workflows/docs.yaml/badge.svg)
![Tests Status](https://github.com/iporepos/copyme/actions/workflows/tests.yaml/badge.svg)


<a logo>
<img src="https://raw.githubusercontent.com/iporepos/copyme/master/docs/figs/logo.png" height="130" width="130">
</a>

---

# copyme

A simple template for python development. Use this repository as a template for developing a python library or package.

> [!NOTE]
> Check out the [documentation website](https://iporepos.github.io/copyme/)

---

# Templates

When copying files from this repo, remember that they are _templates_. So:

1) look for `[CHANGE THIS]` for mandatory modifications;
2) look for `[CHECK THIS]` for possible modifications;
3) look for `[EXAMPLE]` for simple examples (comment or uncomment it if needed);
4) look for `[ADD MORE IF NEDDED]` for possible extra features;
5) placeholders are designated by curly braces: `{replace-this}`.


---

# Configuration files

This repository relies on several **configuration files** that are essential for the proper functioning of the template. Each file has a specific role, and some of them work together, so they should be edited thoughtfully. Below is an overview of the main configuration files and what you should know about them.


| File                               | Purpose | Key Notes |
|------------------------------------|---------|-----------|
| **`pyproject.toml`**               | Project configuration | Manages dependencies, build system, and project settings. Update when adding dependencies or changing project structure. |
| **`.gitignore`**                   | Git ignore rules | Specifies files/folders Git should ignore (e.g., temp files, datasets, build outputs). Keeps repo clean. |
| **`.github/workflows/style.yaml`** | Style CI configuration | Runs code style checks using [Black](https://black.readthedocs.io/en/stable/). Depends on `pyproject.toml` dev dependencies. |
| **`docs/conf.py`**                 | Docs configuration | Configures [Sphinx](https://www.sphinx-doc.org/en/master/index.html) for building documentation. Update if project structure changes. |
| **`.github/workflows/docs.yaml`**  | Docs CI configuration | Automates online docs build. Relies on `pyproject.toml` and `docs/conf.py`. Requires extra steps (see file). |
| **`tests/conftest.py`**            | Testing configuration | Provides shared fixtures and settings for tests. Can be customized to fit project needs. |
| **`.github/workflows/tests.yaml`** | Testing CI configuration | Runs automated unit tests on CI. Ensures code correctness after changes. |

> [!NOTE]  
> All config files are commented with recommended actions and extra steps.

> [!WARNING]  
> Online documentation build may require additional setup — check `.github/workflows/docs.yml`.

> [!IMPORTANT]  
> Continous Integration (CI) steup allows for check-ups for commits and not allowing bad code
> to be pushed to the main branch. So Style, Docs and Tests must always pass.

---

# Repo layout

A standard python repo may use the following layout. 
This layout is known as `src` layout, since it stores the source code under a `src/{repo}` folder.

> See more on [flat vs src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/) 

```txt
copyme/
│
├── LICENSE
├── README.md                     # [CHECK THIS] this file (landing page)
├── .gitignore                    # [CHECK THIS] configuration of git vcs ignoring system
├── pyproject.toml                # [CHECK THIS] configuration of python project
├── MANIFEST.in                   # [CHECK THIS] configuration of source distribution
│
├── .venv/                        # [ignored] virtual environment (recommended for development)
│
├── .github/                      # github folder
│    └── workflows/               # folder for continuous integration services
│         ├── style.py            # [CHECK THIS] configuration file for style check workflow
│         ├── tests.py            # [CHECK THIS] configuration file for tests workflow
│         └── docs.yml            # [CHECK THIS] configuration file for docs build workflow
│
├── src/                          # source code folder
│    ├── copyme.egg-info          # [ignored] [generated] files for local development
│    └── copyme/                  # [CHANGE THIS] source code root
│         ├── __init__.py         # template init file
│         ├── module.py           # template module
│         ├── ...                 # develop your modules
│         ├── mypackage/          # template package
│         │    ├── __init__.py
│         │    └── submodule.py
│         └── data/               # run-time data
│              └── src_data.txt   # dummy data file
│
├── tests/                        # testing code folder
│    ├── conftest.py              # [CHECK THIS] configuration file of tests
│    ├──unit/                     # unit tests package     
│    │    ├── __init__.py
│    │    └── test_module.py      # template module for unit tests
│    ├── bcmk/                    # benchmarking tests package
│    │    ├── __init__.py               
│    │    └── test_bcmk.py        # template module for benchmarking tests
│    ├── data/                    # test-only data
│    │     ├── test_data.csv
│    │     ├── datasets.csv       # table of remote datasets
│    │     └── dataset1/          # [ignored] subfolders in data
│    └── outputs/                 # [ignored] tests outputs
│
├── docs/                         # documentation folder
│    ├── docs_update.rst          # updating script
│    ├── about.rst                # info about the repo
│    ├── api.rst                  # api reference using sphinx autodoc
│    ├── conf.py                  # [CHECK THIS] configuration file for sphinx
│    ├── dummy.md                 # markdown docs also works
│    ├── index.rst                # home page for documentation
│    ├── usage.rst                # instructions for using this repo
│    ├── make.bat                 # (optional) [generated] sphinx auxiliar file 
│    ├── Makefile                 # (optional) [generated] sphinx auxiliar file 
│    ├── figs/                    # figs-only files
│    │    ├── logo.png
│    │    ├── logo.svg
│    │    └── fig1.png               
│    ├── data/                    # docs-only data
│    │    └── docs.txt            # dummy data file
│    ├── generated/               # [generated] sphinx created files 
│    ├── _templates/              # [ignored] [generated] sphinx created stuff
│    ├── _static/                 # [ignored] [generated] sphinx created stuff
│    └── _build/                  # [ignored] [generated] sphinx build
│
└── examples/                     # (optional) learning resources 
     ├── examples_01.ipynb    
     └── examples_02.ipynb            

```
