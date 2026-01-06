# Dummy file

This is a Markdown (`md`) file used for documentation under Sphinx. 

The extension `myst_parser` of Sphinx allows conversion to HTML during the
build process. This is not a built-in extension, and must be listed in the `pyproject.toml` file:

```toml
# Documentation dependencies 
# =======================================================================
# install with `pip install -e ".[docs]"`
docs = [
    "sphinx",                       # [EXAMPLE] Documentation generator
    "sphinx-autodoc-typehints",     # [EXAMPLE] Include Python type hints in docs
    "sphinx-rtd-theme",             # [EXAMPLE] Sphinx theme
    "pydata-sphinx-theme",          # [EXAMPLE] Sphinx theme
    "sphinx_copybutton",            # [EXAMPLE] Sphinx feature for code blocks
    "myst-parser",                  # <--- Sphinx feature for markdown files
    # ... [ADD MORE IF NEDDED]
]
```

```{note}
Is better to stay in `rst` format, but this extension allows more flexibility.
```

```{warning}
The above admoenition note (and this) is written in the `myst_parser` compatible format
```



