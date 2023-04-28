CHANGELOG
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

--------------------------------------------------------------------------------

Unreleased
----------

`Differences from 0.3.8`_

--------------------------------------------------------------------------------

Release 0.3.8 - 2023-04-27
--------------------------

CODENAME: `DiscoVision`_

You found me again, welcome back

`Release 0.3.8`_

`Differences from 0.3.7`_

Purpose
+++++++

Add autotune logic


Affected Issues
+++++++++++++++

- `#205 Add logic to suggest tuning parameters`_

- `#201 Add missing visualization conversion update`_

Changed
+++++++

- ``-visualize`` added to old project files

Added
+++++

- brr handling logic

- autotune support

Removed
+++++++

None

Idiosyncrasies
++++++++++++++

- Lightly tested on windows, watch out for problems on that OS

- All tests are broken

--------------------------------------------------------------------------------

Release 0.3.7 - 2023-04-06
--------------------------

CODENAME: `Sabotage`_

Oh my God, it's a mirage

I'm tellin' y'all, it's a sabotage

`Release 0.3.7`_

`Differences from 0.3.6`_

Purpose
+++++++

Add ARAM estimation logic


Affected Issues
+++++++++++++++

- `#199 Add BRR file size display`_

- `#198 Add ARAM calculation`_

- `#190 Validate musicxml on load`_

Changed
+++++++

- All projects get #optimized, even if there are no custom samples

Added
+++++

- ARAM utilization graph in bottom right

- MML and SPC generation steps are run at MusicXML load time

  - Gives you an initial idea of your utilization and any glaring errors

- BRR file/sample sizes are displayed in UI

- Ctrl+R as a shortcut for render

Removed
+++++++

None

Idiosyncrasies
++++++++++++++

- Lightly tested on windows, watch out for problems on that OS

- All tests are broken

--------------------------------------------------------------------------------

Release 0.3.6 - 2023-04-01
--------------------------

CODENAME: `La Forme`_

Inspiration

Expiration

Contraction

Décontraction

La forme

`Release 0.3.6`_

`Differences from 0.3.5`_

Purpose
+++++++

Finally fix broken initial q values


Affected Issues
+++++++++++++++

- `#189 Update default q values`_

- `#188 Move start measure`_

- `#187 Prompt "are you sure" on rendering`_

- `#152 Broken initial q values`_

Changed
+++++++

- Start measure, just do it, render, and reload xml moved to below main UI

  - Makes collapsing the control panel easier to do

- Changed default articulation settings

Added
+++++

- Instrument q values are set to default when an instrument is chosen

- Prompt on render option

Removed
+++++++

None

Idiosyncrasies
++++++++++++++

- Lightly tested on windows, watch out for problems on that OS

- All tests are broken

--------------------------------------------------------------------------------

Release 0.3.5 - 2023-03-30
--------------------------

CODENAME: `Cherry Twist`_

That's right

Have more rhythm

Woooo!

`Release 0.3.5`_

`Differences from 0.3.4`_

Purpose
+++++++

Fix new project creation bug


Affected Issues
+++++++++++++++

- `#186 Error in saving projects`_

Changed
+++++++

Fixed incorrect type conversion

Added
+++++

None

Removed
+++++++

None

Idiosyncrasies
++++++++++++++

- Lightly tested on windows, watch out for problems on that OS

- All tests are broken

--------------------------------------------------------------------------------

Release 0.3.4 - 2023-03-25
--------------------------

CODENAME: `I'm Pissed`_

You won't like me 'til I've had my dance.

`Release 0.3.4`_

`Differences from 0.3.3`_

Purpose
+++++++

Add multisample and proper percussion support


Affected Issues
+++++++++++++++

- `#184 Apply fix to bonus ending builtin song`_

- `#182 Update drm file`_

- `#180 Auto-select sample pack when one is picked`_

- `#179 Alert on new release`_

- `#175 Interpolate check box sometimes takes multiple clicks`_

- `#172 UI likes to retain prior project information`_

- `#171 Double click prj files to open`_

- `#170 Invert ADSR sliders`_

- `#169 Reloading xml doesn't catch new dynamics`_

- `#164 Verify open/save/close/create project permutations are saftey`_

- `#162 Multiple instruments using the same samples breaks conversion`_

- `#159 Final mix button`_

- `#156 History window has the wrong title`_

- `#154 Add history edit menu item`_

- `#153 Custom sample selections are broken`_

- `#150 Sample folder watching`_

- `#136 Add multisample definition support`_

- `#130 Automatic optimized percussion handling`_

- `#95 Triplet bug`_

- `#94 Per-note sample definition`_

- `#90 Add proper artic/pan/dynamics support for percussion`_

Changed
+++++++

- Save file version updated

  - We best-effort an upgrade and save a backup

- Sample pack selections are cleared when changing to a sample that doesn't use
  them

- Old ``octave`` setting is now an ``octave shift``; semantics are slightly
  different

- ADSR sliders flipped upside down so "more of X" is higher

- "Just do it" hotkey changed to Ctrl+Space

- SPC generation timeout changed to 15s

- Bail on "just do it" if there was an error in MML or SPC generation

- Load projects even when no musicxml is found

- Error on opening missing project files

- UI elements are cleared on project close

- Changed pan mid left/right values

- Custom samples go in a ``#path``

- DRM file changes to put all instruments on voice 0

  - Added a MuseScore v4 drm file

- History window title

- Instrument UI element looks a little different

Added
+++++

- Dark mode

- Per-note sample definitions

  - This enables using multiple brr files for a single instrument based on a
    note range

  - Also enables custom percussion kits

  - Now there are ``instruments``, which can have multiple ``samples``;
    defaults to a single sample, just like previously

  - An instrument named ``Drumset`` is auto-populated with a fully featured kit

- First-class support for percussion, including artic, pan, and dynamics

- Sample folder watching---new samples are automatically found

- ``.prj`` files can be opened by double-clicking or as a CLI dashboard
  argument

- Sample pack and builtin sources are automatically chosen when a sample or
  builtin is chosen

- Automatic handling for vanilla vs. custom percussion samples

- An alert on new releases from github

- Logic to handle blankl ines and comments in sample packs

- Render/mixdown button

- History menu item under "Edit"

- Versioning to preferences file

- Logic to remove a glitch at the end of a builtin song

Removed
+++++++

- QML plugin

Idiosyncrasies
++++++++++++++

- Lightly tested on windows, watch out for problems on that OS

- All tests are broken

--------------------------------------------------------------------------------

Release 0.3.3 - 2023-03-02
--------------------------

`Release 0.3.3`_

`Differences from 0.3.2`_

Purpose
+++++++

Incorporate feedback on the v0.3.2 release, mostly feature additions.


Affected Issues
+++++++++++++++

- `#147 Slurs in triplets are broken`_

- `#146 Emit error messages if AMK zip and SPC player are not set`_

- `#144 MML generation asserts when not used in project mode`_

- `#143 Windows poetry build failures`_

- `#100 Slur starting/ending on the same note`_

- `#95 Triplet bug`_


Changed
+++++++

- Ties/slurs in triplets no longer broken

- Juxtaposed slurs/ties no longer broken

- Fixed "assert on MML generation in non-project mode"

- Switched to using a Qt resource file for data artifacts

- Poetry version pinned

Added
+++++

- Project mode UI elements are disabled if AMK and spcplayer aren't set

  - Tooltips on those elements describe how to set those preferences

- Icons

Removed
+++++++

- All webserver components and dependencies

Idiosyncrasies
++++++++++++++

- Lightly tested on windows, watch out for problems on that OS

--------------------------------------------------------------------------------

Release 0.3.2 - 2023-02-27
--------------------------

`Release 0.3.2`_

`Differences from 0.3.1`_

Purpose
+++++++

Incorporate feedback on the v0.3.1 release, mostly feature additions.


Affected Issues
+++++++++++++++

- `#140 Hide global legato behind advanced`_

- `#138 Some ability to start from measure #X`_

- `#137 Update mermaid.js deps`_

- `#135 Surround support for panning`_

- `#134 Solo and mute are broken for percussion channels`_

- `#133 Make custom samples directory match the project name`_

- `#132 Echo channel mapping error`_

- `#131 SPC conversion error w/o MML generation`_


Changed
+++++++

- Preferences hotkey changed to control+,

- Changed custom samples subdirectory to match the project name

- Fixed incorrect echo channel ordering

- Instrument name reported in UI status updates

- ``Superloop Analysis`` checkbox grayed out for the time being

- ``Preview`` window button renamed ``Envelope Preview`` to clear up
  confusion about its purpose


Added
+++++

- Percussion solo/mute functionality

  - Current implementation is stopgap

- Pan surround support

- Option to start outputting music after measure 1

  - This implicitly disables loop detection

  - Might behave strangely if there are crescendos that cross the
    starting measure, or if you start after the initial repeat point and
    listen across the repeat

- Advanced mode in preferences

  - When disabled (default), global echo, generate MML, generate SPC,
    and play SPC UI elements are hidden

  - Defaults to "off", with global echo defaulted to "on"

- Explicit warnings when trying to convert a non-existent MML file, or
  play a non-existent SPC file

- Tooltips for echo inversion checkboxes

Removed
+++++++

- Webserver deployment github action

Idiosyncrasies
++++++++++++++

- Lightly tested on windows, watch out for problems on that OS

--------------------------------------------------------------------------------

Release 0.3.1 - 2023-02-20
--------------------------

`Release 0.3.1`_

`Differences from 0.3.0`_

Purpose
+++++++

Cleanup a few warts in v0.3.0


Affected Issues
+++++++++++++++

- `#129 Add porter and game name to UI`_

- `#128 Put custom samples in a specific subdir`_

- `#126 Select an instrument after loading`_

- `#125 Replace discrete sample packs with a sample pack directory`_

- `#124 Sample file parsing error`_

- `#113 Display human readable interpretations of ADSR and gain settings`_

- `#112 Improve envelope display performance`_


Changed
+++++++

- Fixed quicklook using non-monospace font on windows

- Fixed broken undo/redo while working in a project

- BRR files are placed in a subdirectory of ``samples``

- Streamlined envelope calculations

- On project load, first instrument is selected automatically

- Sample packs now come from a user-provided directory rather than being
  registered one-by-one

Added
+++++

- Space is a shortcut for "convert and play"

- Porter and game name entries in the UI

  - These can be pulled in from the score; if used in the UI, those
    values are overridden

- Human-readable ADSR/gain values


Removed
+++++++

None

Idiosyncrasies
++++++++++++++

- Lightly tested on windows, watch out for problems on that OS

--------------------------------------------------------------------------------

Release 0.3.0 - 2023-02-19
--------------------------

`Release 0.3.0`_

`Differences from 0.2.3`_

Purpose
+++++++

First big step towards making this tool a one-stop-shop for porting music.
What a difference a year makes.


Affected Issues
+++++++++++++++

- `#122 Detect if AMK fails`_

- `#121 Add close project functionality`_

- `#119 Fix "would you like to save" when closing subwindows`_

- `#118 Fix instrument updating logic`_

- `#117 Autosave`_

- `#116 Don't prompt to save on newly opened project`_

- `#114 Spurious updates to BRR settings`_

- `#111 Finish all-in-one windows compatibility`_

- `#110 Echo values are broken in MML writes`_

- `#105 Add solo/mute options to UI`_

- `#101 Extraneous python deps`_

- `#97 Dynamics limits`_

- `#93 Incorrect KDn immediately following SNn commands`_

- `#92 Explicit default q values`_

- `#56 Include octave definitions in instrument macros?`_


Changed
+++++++

- Totally reworked UI to use qtdesigner

  - Some reorganization of UI elements

- Moved python package to beta

Added
+++++

- Project-based workflow

- Generate and play SPC files directly from UI

- Native support for BRR samples and sample packs

- Instrument solo/mute functionality

- Support for modifying instrument tuning and envelopes

  - Can use both UI elements or raw BRR settings

- Envelope viewer

- History viewer

- Undo/redo support


Removed
+++++++

- UI tests

  - These were breaking hard; left them in place, just marked
    as unused.  Can be recovered later.

Idiosyncrasies
++++++++++++++

- Lightly tested on windows, watch out for problems on that OS


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

.. _#205 Add logic to suggest tuning parameters: https://github.com/com-posers-pit/smw_music/issues/205
.. _#201 Add missing visualization conversion update: https://github.com/com-posers-pit/smw_music/issues/201
.. _#199 Add BRR file size display: https://github.com/com-posers-pit/smw_music/issues/199
.. _#198 Add ARAM calculation: https://github.com/com-posers-pit/smw_music/issues/198
.. _#190 Validate musicxml on load: https://github.com/com-posers-pit/smw_music/issues/190
.. _#189 Update default q values: https://github.com/com-posers-pit/smw_music/issues/189
.. _#188 Move start measure: https://github.com/com-posers-pit/smw_music/issues/188
.. _#187 Prompt "are you sure" on rendering: https://github.com/com-posers-pit/smw_music/issues/187
.. _#186 Error in saving projects: https://github.com/com-posers-pit/smw_music/issues/186
.. _#184 Apply fix to bonus ending builtin song: https://github.com/com-posers-pit/smw_music/issues/184
.. _#182 Update drm file: https://github.com/com-posers-pit/smw_music/issues/182
.. _#180 Auto-select sample pack when one is picked: https://github.com/com-posers-pit/smw_music/issues/180
.. _#179 Alert on new release: https://github.com/com-posers-pit/smw_music/issues/179
.. _#175 Interpolate check box sometimes takes multiple clicks: https://github.com/com-posers-pit/smw_music/issues/175
.. _#172 UI likes to retain prior project information: https://github.com/com-posers-pit/smw_music/issues/172
.. _#171 Double click prj files to open: https://github.com/com-posers-pit/smw_music/issues/171
.. _#170 Invert ADSR sliders: https://github.com/com-posers-pit/smw_music/issues/170
.. _#169 Reloading xml doesn't catch new dynamics: https://github.com/com-posers-pit/smw_music/issues/169
.. _#164 Verify open/save/close/create project permutations are saftey: https://github.com/com-posers-pit/smw_music/issues/164
.. _#162 Multiple instruments using the same samples breaks conversion: https://github.com/com-posers-pit/smw_music/issues/162
.. _#159 Final mix button: https://github.com/com-posers-pit/smw_music/issues/159
.. _#156 History window has the wrong title: https://github.com/com-posers-pit/smw_music/issues/156
.. _#154 Add history edit menu item: https://github.com/com-posers-pit/smw_music/issues/154
.. _#153 Custom sample selections are broken: https://github.com/com-posers-pit/smw_music/issues/153
.. _#152 Broken initial q values: https://github.com/com-posers-pit/smw_music/issues/152
.. _#150 Sample folder watching: https://github.com/com-posers-pit/smw_music/issues/150
.. _#147 Slurs in triplets are broken: https://github.com/com-posers-pit/smw_music/issues/147
.. _#146 Emit error messages if AMK zip and SPC player are not set: https://github.com/com-posers-pit/smw_music/issues/146
.. _#144 MML generation asserts when not used in project mode: https://github.com/com-posers-pit/smw_music/issues/144
.. _#143 Windows poetry build failures: https://github.com/com-posers-pit/smw_music/issues/143
.. _#140 Hide global legato behind advanced: https://github.com/com-posers-pit/smw_music/issues/140
.. _#138 Some ability to start from measure #X: https://github.com/com-posers-pit/smw_music/issues/138
.. _#137 Update mermaid.js deps: https://github.com/com-posers-pit/smw_music/issues/137
.. _#136 Add multisample definition support: https://github.com/com-posers-pit/smw_music/issues/136
.. _#135 Surround support for panning: https://github.com/com-posers-pit/smw_music/issues/135
.. _#134 Solo and mute are broken for percussion channels: https://github.com/com-posers-pit/smw_music/issues/134
.. _#133 Make custom samples directory match the project name: https://github.com/com-posers-pit/smw_music/issues/133
.. _#132 Echo channel mapping error: https://github.com/com-posers-pit/smw_music/issues/132
.. _#131 SPC conversion error w/o MML generation: https://github.com/com-posers-pit/smw_music/issues/131
.. _#130 Automatic optimized percussion handling: https://github.com/com-posers-pit/smw_music/issues/130
.. _#129 Add porter and game name to UI: https://github.com/com-posers-pit/smw_music/issues/129
.. _#128 Put custom samples in a specific subdir: https://github.com/com-posers-pit/smw_music/issues/128
.. _#126 Select an instrument after loading: https://github.com/com-posers-pit/smw_music/issues/126
.. _#125 Replace discrete sample packs with a sample pack directory: https://github.com/com-posers-pit/smw_music/issues/125
.. _#124 Sample file parsing error: https://github.com/com-posers-pit/smw_music/issues/124
.. _#122 Detect if AMK fails: https://github.com/com-posers-pit/smw_music/issues/122
.. _#121 Add close project functionality: https://github.com/com-posers-pit/smw_music/issues/121
.. _#119 Fix "would you like to save" when closing subwindows: https://github.com/com-posers-pit/smw_music/issues/119
.. _#118 Fix instrument updating logic: https://github.com/com-posers-pit/smw_music/issues/118
.. _#117 Autosave: https://github.com/com-posers-pit/smw_music/issues/117
.. _#116 Don't prompt to save on newly opened project: https://github.com/com-posers-pit/smw_music/issues/116
.. _#114 Spurious updates to BRR settings: https://github.com/com-posers-pit/smw_music/issues/114
.. _#113 Display human readable interpretations of ADSR and gain settings: https://github.com/com-posers-pit/smw_music/issues/113
.. _#112 Improve envelope display performance: https://github.com/com-posers-pit/smw_music/issues/112
.. _#111 Finish all-in-one windows compatibility: https://github.com/com-posers-pit/smw_music/issues/111
.. _#110 Echo values are broken in MML writes: https://github.com/com-posers-pit/smw_music/issues/110
.. _#105 Add solo/mute options to UI: https://github.com/com-posers-pit/smw_music/issues/105
.. _#101 Extraneous python deps: https://github.com/com-posers-pit/smw_music/issues/101
.. _#100 Slur starting/ending on the same note: https://github.com/com-posers-pit/smw_music/issues/100
.. _#97 Dynamics limits: https://github.com/com-posers-pit/smw_music/issues/97
.. _#95 Triplet bug: https://github.com/com-posers-pit/smw_music/issues/95
.. _#94 Per-note sample definition: https://github.com/com-posers-pit/smw_music/issues/94
.. _#93 Incorrect KDn immediately following SNn commands: https://github.com/com-posers-pit/smw_music/issues/93
.. _#92 Explicit default q values: https://github.com/com-posers-pit/smw_music/issues/92
.. _#90 Add proper artic/pan/dynamics support for percussion: https://github.com/com-posers-pit/smw_music/issues/90
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

.. _Release 0.3.8: https://github.com/com-posers-pit/smw_music/releases/tag/v0.3.8
.. _Release 0.3.7: https://github.com/com-posers-pit/smw_music/releases/tag/v0.3.7
.. _Release 0.3.6: https://github.com/com-posers-pit/smw_music/releases/tag/v0.3.6
.. _Release 0.3.5: https://github.com/com-posers-pit/smw_music/releases/tag/v0.3.5
.. _Release 0.3.4: https://github.com/com-posers-pit/smw_music/releases/tag/v0.3.4
.. _Release 0.3.4: https://github.com/com-posers-pit/smw_music/releases/tag/v0.3.4
.. _Release 0.3.3: https://github.com/com-posers-pit/smw_music/releases/tag/v0.3.3
.. _Release 0.3.2: https://github.com/com-posers-pit/smw_music/releases/tag/v0.3.2
.. _Release 0.3.1: https://github.com/com-posers-pit/smw_music/releases/tag/v0.3.1
.. _Release 0.3.0: https://github.com/com-posers-pit/smw_music/releases/tag/v0.3.0
.. _Release 0.2.3: https://github.com/com-posers-pit/smw_music/releases/tag/v0.2.3
.. _Release 0.2.2: https://github.com/com-posers-pit/smw_music/releases/tag/v0.2.2
.. _Release 0.2.1: https://github.com/com-posers-pit/smw_music/releases/tag/v0.2.1
.. _Release 0.2.0: https://github.com/com-posers-pit/smw_music/releases/tag/v0.2.0
.. _Release 0.1.2: https://github.com/com-posers-pit/smw_music/releases/tag/v0.1.2
.. _Release 0.1.1: https://github.com/com-posers-pit/smw_music/releases/tag/v0.1.1
.. _Release 0.1.0: https://github.com/com-posers-pit/smw_music/releases/tag/v0.1.0

.. _Differences from 0.3.8: https://github.com/com-posers-pit/smw_music/compare/v0.3.8...HEAD
.. _Differences from 0.3.7: https://github.com/com-posers-pit/smw_music/compare/v0.3.7...v0.3.8
.. _Differences from 0.3.6: https://github.com/com-posers-pit/smw_music/compare/v0.3.6...v0.3.7
.. _Differences from 0.3.5: https://github.com/com-posers-pit/smw_music/compare/v0.3.5...v0.3.6
.. _Differences from 0.3.4: https://github.com/com-posers-pit/smw_music/compare/v0.3.4...v0.3.5
.. _Differences from 0.3.3: https://github.com/com-posers-pit/smw_music/compare/v0.3.3...v0.3.4
.. _Differences from 0.3.2: https://github.com/com-posers-pit/smw_music/compare/v0.3.2...v0.3.3
.. _Differences from 0.3.1: https://github.com/com-posers-pit/smw_music/compare/v0.3.1...v0.3.2
.. _Differences from 0.3.0: https://github.com/com-posers-pit/smw_music/compare/v0.3.0...v0.3.1
.. _Differences from 0.2.3: https://github.com/com-posers-pit/smw_music/compare/v0.2.3...v0.3.0
.. _Differences from 0.2.2: https://github.com/com-posers-pit/smw_music/compare/v0.2.2...v0.2.3
.. _Differences from 0.2.1: https://github.com/com-posers-pit/smw_music/compare/v0.2.1...v0.2.2
.. _Differences from 0.2.0: https://github.com/com-posers-pit/smw_music/compare/v0.2.0...v0.2.1
.. _Differences from 0.1.2: https://github.com/com-posers-pit/smw_music/compare/v0.1.2...v0.2.0
.. _Differences from 0.1.1: https://github.com/com-posers-pit/smw_music/compare/v0.1.1...v0.1.2
.. _Differences from 0.1.0: https://github.com/com-posers-pit/smw_music/compare/v0.1.0...v0.1.1

.. _DiscoVision: https://www.youtube.com/watch?v=Azsk21MpbUk
.. _Sabotage: https://www.youtube.com/watch?v=z5rRZdiu1UE
.. _La Forme: https://www.youtube.com/watch?v=-TEL_PPSt4s
.. _Cherry Twist: https://www.youtube.com/watch?v=eLkQ2eLrUMs
.. _I'm Pissed: https://www.youtube.com/watch?v=T6dmMUR9TVI
