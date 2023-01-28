Dashboard Signal/Slot Map
=========================

This page includes the mapping between all signals and slots in the dashboard
application.
The documentation must be manually updated any time they change, so anything
that's out of date should be reported.

Control Panel
-------------

.. mermaid::

   flowchart LR
      view.select_musicxml_fname.clicked --> view.on_musicxml_fname_selected
      view.musicxml_fname.textChanged --> model.on_musicxml_changed
      view.select_mml_fname.clicked --> view.on_mml_fname_selected
      view.mml_fname.textChanged --> model.on_mml_changed
      view.loop_analysis.stateChanged --> model.on_loop_analysis_change
      view.superloop_analysis.stateChanged --> model.on_superloop_analysis_change
      view.measure_numbers.stateChanged --> model.on_measure_numbers_change
      view.open_quicklook.clicked --> view.on_quicklook_opened
      view.generate_mml.clicked --> model.on_mml_generated
      view.generate_spc.clicked --> model.on_spc_generated
      view.play_spc.clicked --> model.on_spc_played

Instrument Settings
-------------------

Instruments
~~~~~~~~~~~

.. mermaid::

   flowchart LR
      view.instrument_list.



Dynamics
~~~~~~~~

.. mermaid::

   flowchart LR

Articulations
~~~~~~~~~~~~~

.. mermaid::

   flowchart LR

Pan
~~~

.. mermaid::

   flowchart LR

Sample
~~~~~~

.. mermaid::

   flowchart LR

Global Settings
---------------

Global Volume
~~~~~~~~~~~~~

.. mermaid::

   flowchart LR
     view.global_legato.stateChanged --> model.on_global_legato_change
