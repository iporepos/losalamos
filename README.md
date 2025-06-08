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

## 🍞🧈 Install via uv
Get [uv](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer) package manager
```bash
# Install uv system-wise via pipx (if it is not installed)
pip install pipx
pipx install uv

# Create a virtual environment 
uv venv

# Update the project's environment (get libs)
uv sync

# Activate it
.venv/Scripts/activate     # Windows
source .venv/bin/activate  # Linux

# --- Package manager (uv) ---
# [Un-]install dependencies
uv add/remove --dev black numpy<2
```

## Development
- Formatting
```bash
# Follow PEP8 and more (like black)
uv run ruff format .

# Imports
uv run ruff check . --select I --fix
```