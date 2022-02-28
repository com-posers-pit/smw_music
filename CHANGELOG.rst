CHANGELOG
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

--------------------------------------------------------------------------------

Unreleased
----------

`Differences from 0.2.3`_

--------------------------------------------------------------------------------

Release 0.2.3 - 2022-02-27
--------------------------

`Release 0.2.3`_

`Differences from 0.2.2`_

Purpose
+++++++


Affected Issues
+++++++++++++++

- `#87 Generate a backup mml`_

- `#86 Add vibrato support`_

- `#85 Non-concert pitch instruments`_

- `#84 Dashboard loop analysis bug`_

- `#82 Display generated text`_

Changed
+++++++

- Fix bug where multiple exports in the dashboard broke things spectacularly

- Moved python package to alpha

- Strip unicode from instrument names, except flat which goes to 'b'

Added
+++++

- Quicklook window

- MML file backup generation

- Initial vibrato support

- Logic to support transposing instruments
  - Temporarily removed due to a bug in music21

- Testing updates
  - GUI tests

  - Github action to run tests on windows runners

Removed
+++++++

None.

Idiosyncrasies
++++++++++++++

None.

--------------------------------------------------------------------------------

Release 0.2.2 - 2022-02-22
--------------------------

`Release 0.2.2`_

`Differences from 0.2.1`_

Purpose
+++++++

Fix extra newline problem in output on windows

Affected Issues
+++++++++++++++

- `#80 Extra newlines in windows-generated output`_

Changed
+++++++

- Removed extra newlines in .exe-generated MML outputs
  - This was a side effect of print in text mode on windows

Added
+++++

None.

Removed
+++++++

None.

Idiosyncrasies
++++++++++++++

None.

--------------------------------------------------------------------------------

Release 0.2.1 - 2022-02-21
--------------------------

`Release 0.2.1`_

`Differences from 0.2.0`_

Purpose
+++++++

Fix problem in GH publish action---no changes to the codebase.

See `Release 0.2.0`_ for applicable changelog.

Affected Issues
+++++++++++++++

None.

Changed
+++++++

None.

Added
+++++

None.

Removed
+++++++

None.

Idiosyncrasies
++++++++++++++

None.

--------------------------------------------------------------------------------

Release 0.2.0 - 2022-02-21
--------------------------

`Release 0.2.0`_

`Differences from 0.1.2`_

Purpose
+++++++

Major overhaul, adding GUI support and moving towards a completely declarative
MML file

Affected Issues
+++++++++++++++

- `#78 Interpolation crash w/ ffff slider`_
- `#76 Support multiple tempos`_
- `#73 "complex" error`_
- `#72 Staff ends in a triplet`_
- `#71 Report all errors at once`_
- `#70 Remove l directives for empty sections`_
- `#69 Use "^" for accented staccato`_
- `#68 Slider-based control for per-instrument dynamics, pan, artic in GUI`_
- `#67 UI with faders for volume, q values, y values, ....`_
- `#65 Rename crash/ride w/ numbers`_
- `#64 Distinguish crescendo/decrescendo in macro names`_
- `#59 Per-instrument dynamics`_
- `#58 Support non-common time signatures`_
- `#56 Include octave definitions in instrument macros?`_
- `#54 Crescendo fades to same dynamic`_
- `#52 Equals align volume macros`_
- `#51 Echo command formatting`_
- `#50 Ensure hex values use uppercase letters`_
- `#49 Swap repeat and instrument annotations`_
- `#47 Measure numbering for loops`_
- `#46 Panning`_
- `#45 Remove redundancies post-reduction`_
- `#44 Loop handling with crescendos and triplets`_
- `#43 Add octave and note name into percussion macros`_
- `#42 Add header boilerplate text for instruments and samples`_
- `#40 toggle percussion mode based on clef`_
- `#37 Show echo delay time in ms, not taps`_
- `#35 Recalculate default octave and length values in each section`_
- `#34 reverb settings`_
- `#33 Musescore plugin`_
- `#32 Don't output measure comments inside a triplet`_
- `#30 apply q values to tied notes`_
- `#29 add measure numbers in comments`_
- `#27 Legato options`_
- `#26 Grace note handling`_
- `#24 Add support for accents and staccatos`_
- `#23 Add initial channel header information`_
- `#22 Use double bar lines to demarcate sections`_
- `#21 Replace legato implementation with *real* ties`_
- `#19 Add exceptions for handling errors`_
- `#15 Add AMK loop point support`_
- `#14 Add AMK support for automatically-detected repeats`_
- `#13 Add support for manually-notated repeats`_
- `#5 Add support for slurs`_
- `#4 Add support for changing dynamics`_
- `#3 Add support for dynamic levels`_
- `#2 Add support for percussion`_

Changed
+++++++

- Use `^` for tied notes

- Volume macro names

- Instrument-specific octave, volume, pan, artic settings

Added
+++++

- Support for:
  - AMK loop-point handling

  - Slurs

  - Configurable global legato option

  - Staccato and accents

  - Loop analysis, including labeled loops

  - Repeated note detection

  - Measure numbering

  - Percussion

  - Echo options

  - Mid-staff instrument changes

  - Crescendo/decrescendo

  - Instrument pans

  - Multiple tempos

- GUI, webserver, and MuseScore plugin UI support

  - Webserver and MuseScore generated outputs include git hash

- Default @, v, y, q settings

- Build date/time in generated MML files

- Checks for note octave and percussion note validity

- Check for chords

- Custom instrument/sample boilerplate output

- Global volume control in GUI


Removed
+++++++

None.

Idiosyncrasies
++++++++++++++

None.

--------------------------------------------------------------------------------

Release 0.1.2 - 2021-12-28
--------------------------

`Release 0.1.2`_

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

Release 0.1.1 - 2021-12-23
--------------------------

`Release 0.1.1`_

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


Release 0.1.0 - 2021-12-23
--------------------------

`Release 0.1.0`_

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


.. _#87 Generate a backup mml: https://github.com/com-posers-pit/smw_music/issues/87
.. _#86 Add vibrato support: https://github.com/com-posers-pit/smw_music/issues/86
.. _#85 Non-concert pitch instruments: https://github.com/com-posers-pit/smw_music/issues/85
.. _#84 Dashboard loop analysis bug: https://github.com/com-posers-pit/smw_music/issues/84
.. _#82 Display generated text: https://github.com/com-posers-pit/smw_music/issues/82
.. _#80 Extra newlines in windows-generated output: https://github.com/com-posers-pit/smw_music/issues/80
.. _#78 Interpolation crash w/ ffff slider: https://github.com/com-posers-pit/smw_music/issues/78
.. _#76 Support multiple tempos: https://github.com/com-posers-pit/smw_music/issues/76
.. _#73 "complex" error: https://github.com/com-posers-pit/smw_music/issues/73
.. _#72 Staff ends in a triplet: https://github.com/com-posers-pit/smw_music/issues/72
.. _#71 Report all errors at once: https://github.com/com-posers-pit/smw_music/issues/71
.. _#70 Remove l directives for empty sections: https://github.com/com-posers-pit/smw_music/issues/70
.. _#69 Use "^" for accented staccato: https://github.com/com-posers-pit/smw_music/issues/69
.. _#68 Slider-based control for per-instrument dynamics, pan, artic in GUI: https://github.com/com-posers-pit/smw_music/issues/68
.. _#67 UI with faders for volume, q values, y values, ....: https://github.com/com-posers-pit/smw_music/issues/67
.. _#65 Rename crash/ride w/ numbers: https://github.com/com-posers-pit/smw_music/issues/65
.. _#64 Distinguish crescendo/decrescendo in macro names: https://github.com/com-posers-pit/smw_music/issues/64
.. _#59 Per-instrument dynamics: https://github.com/com-posers-pit/smw_music/issues/59
.. _#58 Support non-common time signatures: https://github.com/com-posers-pit/smw_music/issues/58
.. _#56 Include octave definitions in instrument macros?: https://github.com/com-posers-pit/smw_music/issues/56
.. _#54 Crescendo fades to same dynamic: https://github.com/com-posers-pit/smw_music/issues/54
.. _#52 Equals align volume macros: https://github.com/com-posers-pit/smw_music/issues/52
.. _#51 Echo command formatting: https://github.com/com-posers-pit/smw_music/issues/51
.. _#50 Ensure hex values use uppercase letters: https://github.com/com-posers-pit/smw_music/issues/50
.. _#49 Swap repeat and instrument annotations: https://github.com/com-posers-pit/smw_music/issues/49
.. _#47 Measure numbering for loops: https://github.com/com-posers-pit/smw_music/issues/47
.. _#46 Panning: https://github.com/com-posers-pit/smw_music/issues/46
.. _#45 Remove redundancies post-reduction: https://github.com/com-posers-pit/smw_music/issues/45
.. _#44 Loop handling with crescendos and triplets: https://github.com/com-posers-pit/smw_music/issues/44
.. _#43 Add octave and note name into percussion macros: https://github.com/com-posers-pit/smw_music/issues/43
.. _#42 Add header boilerplate text for instruments and samples: https://github.com/com-posers-pit/smw_music/issues/42
.. _#40 toggle percussion mode based on clef: https://github.com/com-posers-pit/smw_music/issues/40
.. _#37 Show echo delay time in ms, not taps: https://github.com/com-posers-pit/smw_music/issues/37
.. _#35 Recalculate default octave and length values in each section: https://github.com/com-posers-pit/smw_music/issues/35
.. _#34 reverb settings: https://github.com/com-posers-pit/smw_music/issues/34
.. _#33 Musescore plugin: https://github.com/com-posers-pit/smw_music/issues/33
.. _#32 Don't output measure comments inside a triplet: https://github.com/com-posers-pit/smw_music/issues/32
.. _#30 apply q values to tied notes: https://github.com/com-posers-pit/smw_music/issues/30
.. _#29 add measure numbers in comments: https://github.com/com-posers-pit/smw_music/issues/29
.. _#27 Legato options: https://github.com/com-posers-pit/smw_music/issues/27
.. _#26 Grace note handling: https://github.com/com-posers-pit/smw_music/issues/26
.. _#24 Add support for accents and staccatos: https://github.com/com-posers-pit/smw_music/issues/24
.. _#23 Add initial channel header information: https://github.com/com-posers-pit/smw_music/issues/23
.. _#22 Use double bar lines to demarcate sections: https://github.com/com-posers-pit/smw_music/issues/22
.. _#21 Replace legato implementation with *real* ties: https://github.com/com-posers-pit/smw_music/issues/21
.. _#19 Add exceptions for handling errors: https://github.com/com-posers-pit/smw_music/issues/19
.. _#18 Add support for tied notes: https://github.com/com-posers-pit/smw_music/issues/18
.. _#17 Handle grace notes: https://github.com/com-posers-pit/smw_music/issues/17
.. _#16 Documentation: https://github.com/com-posers-pit/smw_music/issues/16
.. _#15 Add AMK loop point support: https://github.com/com-posers-pit/smw_music/issues/15
.. _#14 Add AMK support for automatically-detected repeats: https://github.com/com-posers-pit/smw_music/issues/14
.. _#13 Add support for manually-notated repeats: https://github.com/com-posers-pit/smw_music/issues/13
.. _#12 Add AMK automatic default note duration: https://github.com/com-posers-pit/smw_music/issues/12
.. _#11 Add AMK automatic default octave selection: https://github.com/com-posers-pit/smw_music/issues/11
.. _#10 Add support for AMK octave up/down commands: https://github.com/com-posers-pit/smw_music/issues/10
.. _#7 Add support for triplets: https://github.com/com-posers-pit/smw_music/issues/7
.. _#6 Add support for dotted notes: https://github.com/com-posers-pit/smw_music/issues/6
.. _#5 Add support for slurs: https://github.com/com-posers-pit/smw_music/issues/5
.. _#4 Add support for changing dynamics: https://github.com/com-posers-pit/smw_music/issues/4
.. _#3 Add support for dynamic levels: https://github.com/com-posers-pit/smw_music/issues/3
.. _#2 Add support for percussion: https://github.com/com-posers-pit/smw_music/issues/2
.. _#1 Add support for AMK annotations: https://github.com/com-posers-pit/smw_music/issues/1

.. _Release 0.2.3: https://github.com/com-posers-pit/smw_music/releases/tag/v0.2.3
.. _Release 0.2.2: https://github.com/com-posers-pit/smw_music/releases/tag/v0.2.2
.. _Release 0.2.1: https://github.com/com-posers-pit/smw_music/releases/tag/v0.2.1
.. _Release 0.2.0: https://github.com/com-posers-pit/smw_music/releases/tag/v0.2.0
.. _Release 0.1.2: https://github.com/com-posers-pit/smw_music/releases/tag/v0.1.2
.. _Release 0.1.1: https://github.com/com-posers-pit/smw_music/releases/tag/v0.1.1
.. _Release 0.1.0: https://github.com/com-posers-pit/smw_music/releases/tag/v0.1.0

.. _Differences from 0.2.3: https://github.com/com-posers-pit/smw_music/compare/v0.2.3...HEAD
.. _Differences from 0.2.2: https://github.com/com-posers-pit/smw_music/compare/v0.2.2...v0.2.3
.. _Differences from 0.2.1: https://github.com/com-posers-pit/smw_music/compare/v0.2.1...v0.2.2
.. _Differences from 0.2.0: https://github.com/com-posers-pit/smw_music/compare/v0.2.0...v0.2.1
.. _Differences from 0.1.2: https://github.com/com-posers-pit/smw_music/compare/v0.1.2...v0.2.0
.. _Differences from 0.1.1: https://github.com/com-posers-pit/smw_music/compare/v0.1.1...v0.1.2
.. _Differences from 0.1.0: https://github.com/com-posers-pit/smw_music/compare/v0.1.0...v0.1.1
