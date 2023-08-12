Contributing
============

Expectations
------------

In the interest of maintaining a clean and organized project, we maintain a
high standard for contributions.
Pull requests that don't meet these standards will need to be reworked before
being accepted into the codebase.

Getting Started
-----------------------

To get started developing, fork and clone the repository.  On your



Conventions
-----------

- `Semantic Versioning`_ for version numbers
- `gitflow`_ branching model for development
- `Numpy`_-style docstrings
- A standard format for `commit messages`_
- In RST files, sentences start on new lines

Tools
-----

The following tools are used by this project:

- `poetry`_ for project dependency management and packaging
- `pylint`_ and `flake8`_ for linting and `pep8`_ compliance checking
- `pytest`_ as a unit test framework
- `pytest-cov`_ for code coverage, and `codecov`_ for coverage history tracking
- `doc8`_ and `pydocstyle`_ for docstring style analysis
- `mypy`_ for static type checking
- `Black`_ for auto-formatting
- `Bandit`_ for python security vulnerability scanning
- `Tox`_ for automatically running version-specific test suites, linting, and
  coverage
- `Sphinx`_ for documentation and `RTD`_ for hosting generated docs
- `Precommit`_ for standard pre-commit hooks
- `Reuse`_ for license compliance checking
- `Pypi`_ for hosting formal releases

Tool Configuration Files
++++++++++++++++++++++++

Locations for all tool configurations is covered in the following table.

=========== ============================  =======================
Tool        File                          Section
----------- ----------------------------  -----------------------
poetry      ``/pyproject.toml``           ``[tool.poetry*]``
poetry      ``/pyproject.toml``           ``[build-system]``
pylint      ``/pyproject.toml``           ``[tool.pylint*]``
flake8      ``/tox.ini``                  ``[flake8]``
pytest      ``/tox.ini``                  ``[testenv]``
pytest-cov  ``/tox.ini``                  ``[testenv]``
pytest-cov  ``/.coveragerc``              All
codecov     ``/codecov.yml``              All
doc8        ``/tox.ini``                  ``[testenv:lint]``
pydocstyle  ``/pyproject.toml``           ``[tool.pydocstyle]``
mypy        ``/tox.ini``                  ``[testenv:mypy]``
Black       ``/pyproject.toml``           ``[tool.black]``
Bandit      ``/pyproject.toml``           ``[tool.bandit]``
tox         ``/tox.ini``                  ``[tox]``
sphinx      ``/doc/source/conf.py``       All
RTD         ``/.readthedocs.yml``         All
Precommit   ``/.pre-commit-config.yaml``  All
Reuse       ``/.reuse/dep5``              All
Pypi        tbd                           tbd
=========== ============================  =======================


GitHub Actions
--------------

TODO

Key External Libraries
----------------------

- `music21`_ for parsing `MusicXML`_ documents and converting them to a
  standard object representation in Python.
- `mako`_ for templating


.. # Links
.. _commit messages: https://cbea.ms/git-commit/
.. _Semantic Versioning: https://semver.org/
.. _Black: https://github.com/psf/black
.. _pytest: https://docs.pytest.org/en/6.2.x/
.. _pytest-cov: https://pytest-cov.readthedocs.io/en/latest/
.. _Numpy: https://numpydoc.readthedocs.io/en/latest/format.html
.. _Bandit: https://github.com/PyCQA/bandit
.. _RTD: https://smw-music.readthedocs.io/en/latest/
.. _Sphinx: https://www.sphinx-doc.org/en/master/
.. _mypy: http://mypy-lang.org/
.. _Pypi: https://pypi.org/project/smw-music/
.. _codecov: https://app.codecov.io/gh/com-posers-pit/smw_music
.. _Reuse: https://api.reuse.software/info/github.com/com-posers-pit/smw_music
.. _Tox: https://tox.wiki/en/latest/
.. _poetry: https://python-poetry.org/
.. _Precommit: https://pre-commit.com/
.. _Music21: https://github.com/cuthbertLab/music21
.. _MusicXML: https://www.w3.org/community/music-notation/
.. _flake8: https://flake8.pycqa.org/en/latest/
.. _pylint: https://pylint.org/
.. _pep8: https://www.python.org/dev/peps/pep-0008/
.. _doc8: https://github.com/pycqa/doc8
.. _mako: https://www.makotemplates.org/
.. _gitflow: https://nvie.com/posts/a-successful-git-branching-model/
.. _pydocstyle: https://github.com/PyCQA/pydocstyle
