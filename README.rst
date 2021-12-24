SMW Music README
================

|bandit-status| |lint-status| |mypy-status| |test-status| |br|
|reuse| |license| |br|
|made-with-python| |made-with-sphinx-doc|

Library and utilities for generating AddMusicK-compatible MML files from
MusicXML.

The tooling has only been tested with exported MusicXML files from MuseScore
3.6.2, but it should work with outputs from other music notation software.

The software (and especially the libraries) are pre-alpha.  APIs may change at
any time for any/no reason.

Installation
------------


from git

from pypi

Usage
-----

command line tool

rtd

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

A copy of the AGPL v3.0 is available `here <License_>`_

Acknowledgements
----------------

- Kipernal, KungFuFurby, and other authors of `AddMusicK`_
- Wakana's `SMW music porting tutorial`_
- Michael Scott Cuthbert and cuthbertLab's `music21 Python library`_

.. # Links
.. _The SMW Music Python Project Authors: https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst
.. _License: https://github.com/com-posers-pit/smw_music/blob/develop/LICENSES/AGPL-3.0-only.txt
.. _Contributor Guide:  https://github.com/com-posers-pit/smw_music/blob/develop/CONTRIBUTING.rst
.. _AddMusicK: https://www.smwcentral.net/?p=section&a=details&id=24994
.. _SMW music porting tutorial: https://www.smwcentral.net/?p=viewthread&t=89606
.. _music21 Python library: https://github.com/cuthbertLab/music21
.. |made-with-python| image:: https://img.shields.io/badge/Made%20with-Python-1f425f.svg
   :target: https://www.python.org/
.. |made-with-sphinx-doc| image:: https://img.shields.io/badge/Made%20with-Sphinx-1f425f.svg
   :target: https://www.sphinx-doc.org/
.. |bandit-status| image:: https://github.com/com-posers-pit/smw_music/actions/workflows/bandit.yml/badge.svg
   :target: https://github.com/
.. |lint-status| image:: https://github.com/com-posers-pit/smw_music/actions/workflows/lint.yml/badge.svg
   :target: https://github.com/
.. |mypy-status| image:: https://github.com/com-posers-pit/smw_music/actions/workflows/mypy.yml/badge.svg
   :target: https://github.com/
.. |test-status| image:: https://github.com/com-posers-pit/smw_music/actions/workflows/test.yml/badge.svg
   :target: https://github.com/
.. |license| image:: https://img.shields.io/badge/License-AGPLv3-blue.svg
.. |reuse| image:: https://api.reuse.software/badge/github.com/com-posers-pit/smw_music
   :target: https://api.reuse.software/info/github.com/com-posers-pit/smw_music

.. # define a hard line break for HTML
.. |br| raw:: html

   <br />
