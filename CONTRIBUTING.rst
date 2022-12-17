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



Web Frontend
------------

This package includes a rudimentary web tool for converting MusicXML files to
MML which uses uses `flask`_ as a web framework, running on Apache 2.24.52 via
`mod_wsgi`_ in a `Docker`_ container.
The GitHub Deploy workflow in ``/.github/workflows/deploy.yml`` shows how to
the container can be built and deployed on any system running Docker.
Briefly, run the following commands in the top level of the project:

.. code-block:: bash

   docker build -t smw_music --build-arg GITHASH=$(git rev-parse --short HEAD) .
   docker run -dit --name smw_music -p 5000:80 smw_music

Then navigate to `localhost:5000` in a web browser.
The ``GITHASH`` argument in the ``docker build`` command appends argument's
value to the reported release number in the generated MML, which assists in
file provenance.
The argument can be omitted, in which case the package version number is used.

Configuration details follow in subsequent sections.

Docker Configuration
++++++++++++++++++++

The ``/.dockerignore`` file is optimized to use a minimal set of files in the
Docker context.
The ``/Dockerfile`` performs the following (with attention paid to ensure
optimal layer caching):

- Start with a base Apache 2.4.52 system
- Install Python3, pip, mod_wsgi, poetry, and clean up the apt caches
- Configure poetry to use the project directory for virtualenv

  - If this step is missing, the python process spawned by mod_wsgi cannot
    will not have permissions to access the virtualenv, and the server will
    fail

- Copy package dependency files into the container and install the standard
  (non-development) and webserver dependencies

  - Separating this step from copying the full project improves caching, since
    the package dependencies are unlikely to change often

- Copy the Apache configuration file and the webserver files to the container

  - These are also unlikely to change often, and give a minor cache improvement

- Copy all project files to the container and install them
- Declare a build-time argument ``GITHASH``, assign it to an environment
  variable ``GITHASH`` that is persisted in the container
- By default, start the http server in the foreground and pass it environment
  variables defining the python virtualenv (``VENV``) and the git hash
  (``GITHASH``)

Apache Configuration
++++++++++++++++++++

The ``/webserver/httpd.conf`` file contains the Apache configuration.
It is a stripped-down version of the default config file provided with the
Docker image, with mod_wsgi enabled.

The server listens on port 80 and routes all HTTP requests to the
``/webserver/upload.wsgi`` file, which is running under mod_wsgi as a daemon
process as the ``www-data`` user, with its python home directory set to the
``VENV`` environment variable (i.e., the directory of the poetry-managed
virtual environment containing the ``smw_music`` package).

Web Frontend Confguration
+++++++++++++++++++++++++

The ``/webserver/upload.wsgi`` web frontend uses flask to handle requests and
routing.
The main UI page is the ``mml_upload`` endpoint (which is the
``/webserver/templates/upload.html`` file).
POST requests are routed to ``mml_uploader``, which passes the uploaded
MusicXML file to the ``smw_music`` package utilities for conversion to MML and
returns the result to the user.


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
.. _Docker: https://www.docker.com
.. _Flask: https://flask.palletsprojects.com/en/2.0.x/
.. _Music21: https://github.com/cuthbertLab/music21
.. _MusicXML: https://www.w3.org/community/music-notation/
.. _flake8: https://flake8.pycqa.org/en/latest/
.. _pylint: https://pylint.org/
.. _pep8: https://www.python.org/dev/peps/pep-0008/
.. _doc8: https://github.com/pycqa/doc8
.. _mako: https://www.makotemplates.org/
.. _gitflow: https://nvie.com/posts/a-successful-git-branching-model/
.. _pydocstyle: https://github.com/PyCQA/pydocstyle
.. _mod_wsgi: https://modwsgi.readthedocs.io/en/master/
