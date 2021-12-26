CHANGELOG
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

--------------------------------------------------------------------------------

Unreleased
----------

`Differences from 0.1.1`_

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
.. _#16 Documentation: https://github.com/com-posers-pit/smw_music/issues/16

.. _#12 Add AMK automatic default note duration: https://github.com/com-posers-pit/smw_music/issues/12
.. _#11 Add AMK automatic default octave selection: https://github.com/com-posers-pit/smw_music/issues/11
.. _#10 Add support for AMK octave up/down commands: https://github.com/com-posers-pit/smw_music/issues/10
.. _#1 Add support for AMK annotations: https://github.com/com-posers-pit/smw_music/issues/1

.. #####################################################################

.. # Releases
.. _0.1.1: https://github.com/com-posers-pit/smw_music/releases/tag/v0.1.1
.. _0.1.0: https://github.com/com-posers-pit/smw_music/releases/tag/v0.1.0

.. # Differences
.. _Differences from 0.1.1: https://github.com/com-posers-pit/smw_music/compare/v0.1.1...HEAD
.. _Differences from 0.1.0: https://github.com/com-posers-pit/smw_music/compare/v0.1.0...v0.1.1
