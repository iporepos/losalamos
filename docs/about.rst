.. _about:

About
############################################

This repository, ``copyme``, is designed as a **template for Python projects** following best practices in modern software development.
It emphasizes:

* **Style-consistent formatting** – code style is automatically enforced using tools like `Black`_, ensuring consistency across the project.
* **Documentation-oriented practices** – project is documented with `Sphinx`_, including docstrings for API auto-generation.
* **Test-driven development** – all features should be covered by unit and benchmark tests. Avoid bulk data in tests; only include small, useful datasets. Large datasets should be downloaded during development.
* **Continuous Integration (CI)** – Tests, Docs and Style checked online for passing or failing before commiting to main.

This template provides a structured starting point including configuration files, example Python modules, and documentation templates to help you quickly set up a project integrated with GitHub.

**Recommended workflow when using this template:**

1. Set up your project structure based on the template.
2. Copy or adapt configuration files (``pyproject.toml``, testing configs, CI/CD workflows).
3. Copy template files for Python modules, data, and documentation (``__init__.py``, Sphinx docs, etc.).
4. Optionally, download the full development source and rename root folders and source packages to fit your project.

Following this approach ensures your project maintains a standardized structure and behavior.

.. _templates:

Templates
********************************************

When copying files from this repository, remember that they are **_templates_**:

1. Look for ``[CHANGE THIS]`` for mandatory modifications.
2. Look for ``[CHECK THIS]`` for optional modifications.
3. Look for ``[EXAMPLE]`` for simple examples (comment or uncomment if needed).
4. Look for ``[ADD MORE IF NEEDED]`` for possible extra features.
5. Placeholders are designated by curly braces: ``{replace-this}``.

.. _config_files:

Configuration files
********************************************

This repository relies on several **configuration files** that are essential for the proper functioning of the template. Each file has a specific role, and some of them work together, so they should be edited thoughtfully. Below is an overview of the main configuration files:

+---------------------------------+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------+
| **File**                        | **Purpose**                | **Key Notes**                                                                                                                         |
+=================================+============================+=======================================================================================================================================+
| ``pyproject.toml``              | Project configuration      | Manages dependencies, build system, and project settings. Update when adding dependencies or changing project structure.              |
+---------------------------------+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------+
| ``.gitignore``                  | Git ignore rules           | Specifies files/folders Git should ignore (e.g., temp files, datasets, build outputs). Keeps repo clean.                              |
+---------------------------------+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------+
| ``.github/workflows/style.yml`` | Style CI configuration     | Runs code style checks using `Black`_. Depends on ``pyproject.toml`` dev dependencies.                                                |
+---------------------------------+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------+
| ``docs/conf.py``                | Docs configuration         | Configures `Sphinx`_ for building documentation. Update if project structure changes.                                                 |
+---------------------------------+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------+
| ``.github/workflows/docs.yml``  | Docs CI configuration      | Automates online docs build. Relies on ``pyproject.toml`` and `docs/conf.py`. Requires extra steps (see file).                        |
+---------------------------------+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------+
| ``tests/conftest.py``           | Testing configuration      | Provides shared fixtures and settings for tests. Can be customized to fit project needs.                                              |
+---------------------------------+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------+
| ``.github/workflows/tests.yml`` | Testing CI configuration   | Runs automated unit tests on CI. Ensures code correctness after changes.                                                              |
+---------------------------------+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------+


.. Note::

   All config files are commented with recommended actions and extra steps.


.. Warning::

   Online documentation build may require additional setup — check ``.github/workflows/docs.yml``.


.. Important::

   Continuous Integration (CI) ensures commits pass style, docs, and tests before merging. Always ensure these checks pass to avoid pushing broken code.


.. _resources:

Resources
********************************************

Helpful references for configuring and extending your project:

* **pyproject.toml specification** – https://peps.python.org/pep-0621/
* **Sphinx documentation** – https://www.sphinx-doc.org/
* **Python unit testing** – https://docs.python.org/3/library/unittest.html
* **Black code formatter** – https://black.readthedocs.io/
* **GitHub Actions** – https://docs.github.com/en/actions
* **GitHub Workflows** – https://docs.github.com/en/actions/using-workflows


.. _links:

.. _Black: https://black.readthedocs.io/

.. _Sphinx: https://www.sphinx-doc.org
