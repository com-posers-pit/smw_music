SMW Music README
================

|bandit-status| |lint-status| |mypy-status| |test-status| |coverage-status|
|package-version| |python-version| |rtd-status| |package-status| |reuse|
|license-tag| |python-style|

Library and utilities for generating AddMusicK-compatible MML files from
MusicXML.

README FIRST
------------

If you want to use the tool, you can ignore the rest of this document.
Ask for more info in com_poser's discord server.

The tooling has only been tested with exported MusicXML files from MuseScore
3.6.2, but it should work with outputs from other music notation software.
Output files are tested against `AddMusicK`_ 1.0.8.

The software (and especially the libraries) are beta.  APIs may change at
any time for any/no reason.

Local Installation
------------------

Use `pip <https://pip.pypa.io/en/stable>`_ to install ``smw_music``:

.. code-block:: bash

   pip install smw_music

Or install from source using `poetry <https://python-poetry.org/>`_:

.. code-block:: bash

   pip install poetry
   git clone https://github.com/com-posers-pit/smw_music
   cd smw_music
   poetry install --only main

Usage
-----

After installing the tools, convert a MusicXML file ``song.mxl`` to an
AddMusicK MML file ``song.txt`` by running the following command:

.. code-block:: bash

   smw_music_xml_to_amk  song.xml song.txt

See `Examples`_ in the official documentation for more detailed examples
and a feature list.

Contributing
------------

Pull requests are welcome.  See our `Contributor Guide`_ for information.

License
-------

The SMW Music Python Project
Copyright (C) 2021  `The SMW Music Python Project Authors`_

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

A copy of the AGPL v3.0 is available `here <AGPL License_>`__.

Acknowledgements
----------------

- Kipernal, KungFuFurby, and other authors of `AddMusicK`_
- Wakana's `SMW music porting tutorial`_
- Michael Scott Cuthbert and cuthbertLab's `music21 Python library`_
- W3C Music Notation Community Group `MusicXML`_

.. # Links
.. _Examples: https://smw-music.readthedocs.io/en/latest/examples.html
.. _The SMW Music Python Project Authors: https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst
.. _AGPL License: https://github.com/com-posers-pit/smw_music/blob/develop/LICENSES/AGPL-3.0-only.txt
.. _Contributor Guide:  https://github.com/com-posers-pit/smw_music/blob/develop/CONTRIBUTING.rst
.. _AddMusicK: https://www.smwcentral.net/?p=section&a=details&id=24994
.. _SMW music porting tutorial: https://www.smwcentral.net/?p=viewthread&t=89606
.. _music21 Python library: https://github.com/cuthbertLab/music21
.. _MusicXML: https://www.w3.org/community/music-notation/
.. |rtd-status| image:: https://readthedocs.org/projects/smw-music/badge/?version=latest
   :target: https://smw-music.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
.. |bandit-status| image:: https://github.com/com-posers-pit/smw_music/actions/workflows/bandit.yml/badge.svg
   :target: https://github.com/com-posers-pit/smw_music/actions/workflows/bandit.yml
   :alt: Bandit status
.. |coverage-status| image:: https://codecov.io/gh/com-posers-pit/smw_music/branch/develop/graph/badge.svg?token=VOG1I6FT1I
   :target: https://codecov.io/gh/com-posers-pit/smw_music
   :alt: Code Coverage
.. |lint-status| image:: https://github.com/com-posers-pit/smw_music/actions/workflows/lint.yml/badge.svg
   :target: https://github.com/com-posers-pit/smw_music/actions/workflows/lint.yml
   :alt: Lint status
.. |mypy-status| image:: https://github.com/com-posers-pit/smw_music/actions/workflows/mypy.yml/badge.svg
   :target: https://github.com/com-posers-pit/smw_music/actions/workflows/mypy.yml
   :alt: MYPY status
.. |test-status| image:: https://github.com/com-posers-pit/smw_music/actions/workflows/test.yml/badge.svg
   :target: https://github.com/com-posers-pit/smw_music/actions/workflows/test.yml
   :alt: Unit test status
.. |license-tag| image:: https://img.shields.io/pypi/l/smw_music
   :target: https://pypi.org/project/smw_music
   :alt: PyPI - License
.. |reuse| image:: https://api.reuse.software/badge/github.com/com-posers-pit/smw_music
   :target: https://api.reuse.software/info/github.com/com-posers-pit/smw_music
   :alt: REUSE Status
.. |package-version| image:: https://img.shields.io/pypi/v/smw_music
   :target: https://pypi.org/project/smw_music
   :alt: PyPI - Package Version
.. |python-version| image:: https://img.shields.io/pypi/pyversions/smw_music
   :target: https://pypi.org/project/smw_music
   :alt: PyPI - Python Version
.. |package-status| image:: https://img.shields.io/pypi/status/smw_music
   :target: https://pypi.org/project/smw_music
   :alt: PyPI - Status
.. |python-style| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
