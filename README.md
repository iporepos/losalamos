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

## 🍞🧈 Install the ol' bread & butter way
```bash
# Create a virtual environment 
#   (some OSs use "python3" instead of "python")
python -m venv .venv

# Activate it
.venv/Scripts/activate     # Windows
source .venv/bin/activate  # Linux

# --- Package manager (pip) ---
# [Un-]install dependencies
pip [un]install package_name
pip [un]install -r requirements.txt

# Print dependencies & pipe them to "requirements.txt"
pip freeze > requirements.txt
```

## Development
- Formatting
```bash
# Follow PEP8 and more
black .

# Imports
isort .
```