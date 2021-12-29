CHANGELOG
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

--------------------------------------------------------------------------------

Unreleased
----------

`Differences from 0.1.2`_

--------------------------------------------------------------------------------

`0.1.2`_ - 2021-12-28
---------------------

`Differences from 0.1.1`_

Purpose
+++++++

Add support for ties, triplets, dots, and simple dynamics

Affected Issues
+++++++++++++++

- `#18 Add support for tied notes`_
- `#17 Handle grace notes`_
- `#16 Documentation`_
- `#7 Add support for triplets`_
- `#6 Add support for dotted notes`_
- `#3 Add support for dynamic levels`_

Changed
+++++++

- Lowered octave mapping by 1

- Generated file includes tool version number

- Cleaned up API documentation

Added
+++++

- Support for:
  - 64th notes

  - Tied notes

  - Triplet notes/rests

  - Grace notes

  - Dynamics levels

  - Dotted notes/rests

- Test coverage GH, RTD configuration

Removed
+++++++

None.

Idiosyncrasies
++++++++++++++

None.

--------------------------------------------------------------------------------

`0.1.1`_ - 2021-12-23
---------------------

`Differences from 0.1.0`_

Purpose
+++++++

First official release.

Affected Issues
+++++++++++++++

- `#16 Documentation`_

Changed
+++++++

- Decomposed monolithic tox configuration and GH actions

Added
+++++

- Proper README

Removed
+++++++

- ``mako``, ``myst-parser`` dependency

Idiosyncrasies
++++++++++++++

None.

--------------------------------------------------------------------------------


`0.1.0`_ - 2021-12-23
---------------------

Purpose
+++++++

Unofficial Initial release, published to `<test.pypi.org>`_ for workflow
tests only.

Supports:

- Composer and title metadata

- Tempo calculation

- Note and rest decoding

- Automatic most-common octave and note/rest length detection

- AMK annotations

Affected Issues
+++++++++++++++

- `#16 Documentation`_
- `#12 Add AMK automatic default note duration`_
- `#11 Add AMK automatic default octave selection`_
- `#10 Add support for AMK octave up/down commands`_
- `#1 Add support for AMK annotations`_


.. #####################################################################

.. # Issues
.. _#18 Add support for tied notes: https://github.com/com-posers-pit/smw_music/issues/18
.. _#17 Handle grace notes: https://github.com/com-posers-pit/smw_music/issues/17
.. _#16 Documentation: https://github.com/com-posers-pit/smw_music/issues/16
.. _#12 Add AMK automatic default note duration: https://github.com/com-posers-pit/smw_music/issues/12
.. _#11 Add AMK automatic default octave selection: https://github.com/com-posers-pit/smw_music/issues/11
.. _#10 Add support for AMK octave up/down commands: https://github.com/com-posers-pit/smw_music/issues/10
.. _#7 Add support for triplets: https://github.com/com-posers-pit/smw_music/issues/7
.. _#6 Add support for dotted notes: https://github.com/com-posers-pit/smw_music/issues/6
.. _#3 Add support for dynamic levels: https://github.com/com-posers-pit/smw_music/issues/3
.. _#1 Add support for AMK annotations: https://github.com/com-posers-pit/smw_music/issues/1

.. #####################################################################

.. # Releases
.. _0.1.2: https://github.com/com-posers-pit/smw_music/releases/tag/v0.1.2
.. _0.1.1: https://github.com/com-posers-pit/smw_music/releases/tag/v0.1.1
.. _0.1.0: https://github.com/com-posers-pit/smw_music/releases/tag/v0.1.0

.. # Differences
.. _Differences from 0.1.2: https://github.com/com-posers-pit/smw_music/compare/v0.1.2...HEAD
.. _Differences from 0.1.1: https://github.com/com-posers-pit/smw_music/compare/v0.1.1...v0.1.2
.. _Differences from 0.1.0: https://github.com/com-posers-pit/smw_music/compare/v0.1.0...v0.1.1
