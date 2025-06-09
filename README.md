# losalamos 🏜️⚛️🤫
_Research tools with python_

Python objects for handling tasks such:
- Managing references;
- Writing papers and reports;
- Drawing figures;
- Plotting data.

Outputs formats include:
- Bib
- Csv
- Html
- Jpg
- Md
- Pdf
- Png
- rST
- Svg
- Tex
## Branches
|Branch name|Description|
|---|---|
|latest|rolling releases|
|dev|developing and testing|

## 🍞🧈 Install via uv
Get [uv](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer) package manager
```bash
# Install uv system-wise via pipx (if it is not installed)
pip install pipx
pipx install uv

# Create a virtual environment 
uv venv

# Activate it
.venv/Scripts/activate     # Windows
source .venv/bin/activate  # Linux

# --- Package manager (uv) ---
# [Un-]install dependencies
uv add/remove --dev black numpy<2
```

✅ Add dependency in your project-repository
```bash
uv add "losalamos@git+https://github.com/ipo-exe/losalamos.git@latest"
```
🔄 Upgrade later
```bash
uv lock --upgrade-package losalamos
uv sync
```


## Development
- Formatting
```bash
# Follow PEP8 and more (like black + isort)
uv run ruff format .

# Imports
uv run ruff check . --select I --fix
```