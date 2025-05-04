# losalamos
Research tools with python

Python objects for handling tasks such:
- Managing references;
- Writing papers and reports;
- Drawing figures;
- Plotting data.

Required dependencies:
- pandas
- numpy
- matplotlib
- PIL

Outputs formats include:
- Bib
- Csv
- Pdf
- Svg
- Jpg
- Png
- Tex
- Html
- Md
- rST

## Install on Windows OS
Get [Poetry](https://python-poetry.org/docs/)
```bash
python -m pip install pipx
python -m pipx ensurepath
# Add pipx to PATH -> "%USERPROFILE%\AppData\Roaming\Python\Python312\Scripts"
# Restart terminal

# Add packages with
poetry add <package_name>

# Install packages
poetry install

# Activate poetry terminal (type "deactivate" to exit)
poetry shell

# Set the interpreter in your IDE
poetry env info --path
```
