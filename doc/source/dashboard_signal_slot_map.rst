Dashboard Signal/Slot Map
=========================

This page includes the mapping between all signals and slots in the dashboard
application.

.. note::
   All ``editingFinished`` signals are connected to slots via a proxy that
   also sends the updated text.
   Not really sure why this isn't the default.
   ¯\\_(ツ)_/¯

   Essentially the same thing is done in the ``sample_pack_list`` signal.

.. note::
   The documentation must be manually updated any time they change, so anything
   that's out of date should be reported.

Dashboard
---------

.. mermaid::

   flowchart LR
      model.state_changed --> dashboard.on_state_changed
      model.mml_generated --> dashboard.on_mml_generated
      model.response_generated --> dashboard.on_response_generated
      model.preferences_changed --> dashboard.on_preferences_changed
      model.sample_packs_changed --> dashboard.on_sample_packs_changed
      model.recent_projects_updated --> dashboard.on_recent_projects_updated
      model.status_updated --> dashboard.on_status_updated
      model.songinfo_changed --> dashboard.on_songinfo_changed

.. note::
   The ``on_recent_projects_updated`` slot creates new actions, which are
   connected back to ``model.on_load``


Menus
-----

.. mermaid::

   flowchart LR
      view.new_project.triggered --> dashboard._create_project
      view.open_project.triggered --> dashboard._open_project
      view.save_project.triggered --> model.on_save
      view.actionClearRecentProjects.triggered --> model.on_recent_projects_cleared
      view.close_project.triggered --> dashboard._on_close_project_clicked --> model.close_project
      view.open_preferences.triggered --> dashboard._open_preferences
      view.exit_dashboard.triggered --> QApplication.quit
      view.undo.triggered --> model.on_undo_clicked
      view.redo.triggered --> model.on_redo_clicked
      view.show_about.triggered --> dashboard._about
      view.show_about_qt.triggered --> QApplication.aboutQt


Control Panel
-------------

.. mermaid::

   flowchart LR
      view.loop_analysis.stateChanged --> model.on_loop_analysis_changed
      view.superloop_analysis.stateChanged --> model.on_superloop_analysis_changed
      view.measure_numbers.stateChanged --> model.on_measure_numbers_changed
      view.start_measure.valueChanged --> model.on_start_measure_changed
      view.start_section.activated --> model.on_start_section_activated
      view.audition_player.pressed --> dashboard._on_audition_start --> model.on_audition_start
      view.audition_player.released --> model.on_audition_stop
      view.reload_musicxml.released --> model.on_reload_musicxml_clicked
      view.generate_mml.released --> model.on_generate_mml_clicked
      view.generate_spc.released --> model.on_generate_spc_clicked
      view.play_spc.released --> model.on_play_spc_clicked
      view.generate_and_play.released --> model.on_generate_and_play_clicked
      view.render_zip.released --> dashboard._on_render_zip_clicked --> model.on_render_zip_clicked

Instrument Settings
-------------------

Instruments
~~~~~~~~~~~

.. mermaid::

   flowchart LR
      view.sample_list.itemChanged --> dashboard._on_solomute_change --> model.on_solomute_changed
      view.sample_list.selectionChanged --> dashboard._on_sample_change --> model.on_sample_changed
      view.octave_shift.valueChanged --> model.on_octave_shift_changed

Dynamics
~~~~~~~~

.. mermaid::

   flowchart LR
      view.pppp_slider.valueChanged --> model.on_dynamics_changed
      view.pppp_setting.editingFinished --> model.on_dynamics_changed
      view.ppp_slider.valueChanged --> model.on_dynamics_changed
      view.ppp_setting.editingFinished --> model.on_dynamics_changed
      view.pp_slider.valueChanged --> model.on_dynamics_changed
      view.pp_setting.editingFinished --> model.on_dynamics_changed
      view.p_slider.valueChanged --> model.on_dynamics_changed
      view.p_setting.editingFinished --> model.on_dynamics_changed
      view.mp_slider.valueChanged --> model.on_dynamics_changed
      view.mp_setting.editingFinished --> model.on_dynamics_changed
      view.mf_slider.valueChanged --> model.on_dynamics_changed
      view.mf_setting.editingFinished --> model.on_dynamics_changed
      view.f_slider.valueChanged --> model.on_dynamics_changed
      view.f_setting.editingFinished --> model.on_dynamics_changed
      view.ff_slider.valueChanged --> model.on_dynamics_changed
      view.ff_setting.editingFinished --> model.on_dynamics_changed
      view.fff_slider.valueChanged --> model.on_dynamics_changed
      view.fff_setting.editingFinished --> model.on_dynamics_changed
      view.ffff_slider.valueChanged --> model.on_dynamics_changed
      view.ffff_setting.editingFinished --> model.on_dynamics_changed
      A["view.interpolate.stateChanged"] --> model.on_interpolate_changed

Articulations
~~~~~~~~~~~~~

.. mermaid::

   flowchart LR
      view.artic_default_length_slider.valueChanged --> model.on_artic_length_changed
      view.artic_default_length_setting.valueChanged --> model.on_artic_length_changed
      view.artic_default_volume_slider.valueChanged --> model.on_artic_volume_changed
      view.artic_default_volume_setting.valueChanged --> model.on_artic_volume_changed
      view.artic_acc_length_slider.valueChanged --> model.on_artic_length_changed
      view.artic_acc_length_setting.valueChanged --> model.on_artic_length_changed
      view.artic_acc_volume_slider.valueChanged --> model.on_artic_volume_changed
      view.artic_acc_volume_setting.valueChanged --> model.on_artic_volume_changed
      view.artic_stacc_length_slider.valueChanged --> model.on_artic_length_changed
      view.artic_stacc_length_setting.valueChanged --> model.on_artic_length_changed
      view.artic_stacc_volume_slider.valueChanged --> model.on_artic_volume_changed
      view.artic_stacc_volume_setting.valueChanged --> model.on_artic_volume_changed
      view.artic_accstac_length_slider.valueChanged --> model.on_artic_length_changed
      view.artic_accstac_length_setting.valueChanged --> model.on_artic_length_changed
      view.artic_accstac_volume_slider.valueChanged --> model.on_artic_volume_changed
      view.artic_accstac_volume_setting.valueChanged --> model.on_artic_volume_changed
      view.pan_enable.valueChanged --> model.on_pan_enable_changed
      view.pan_setting.valueChanged --> model.on_pan_setting_changed
      view.pan_l_invert.stateChanged --> model.on_pan_invert_changed
      view.pan_r_invert.stateChanged --> model.on_pan_invert_changed

Sample
~~~~~~

.. mermaid::

   flowchart LR
      view.select_builtin_sample.toggled --> model.on_builtin_sample_selected
      view.builtin_sample.currentIndexChanged --> model.on_builtin_sample_changed
      view.select_pack_sample.toggled --> model.on_pack_sample_selected
      view.sample_pack_list.itemSelectionChanged --> model.on_pack_sample_changed
      view.select_brr_sample.toggled --> model.on_brr_sample_selected
      view.select_brr_fname.released --> dashboard.on_brr_clicked
      view.brr_fname.editingFinished --> model.on_brr_fname_changed
      view.select_multisample_sample.toggled --> model.on_multisample_sample_selected
      view.select_adsr_mode.toggled --> model.on_select_adsr_mode_selected
      view.gain_mode_direct.toggled --> model.on_gain_direct_selected
      view.gain_mode_inclin.toggled --> model.on_gain_inclin_selected
      view.gain_mode_incbent.toggled --> model.on_gain_incbent_selected
      view.gain_mode_declin.toggled --> model.on_gain_declin_selected
      view.gain_mode_decexp.toggled --> model.on_gain_decexp_selected
      view.gain_slider.valueChanged --> model.on_gain_changed
      view.gain_setting.valueChanged --> model.on_gain_changed
      view.attack_slider.valueChanged --> model.on_attack_changed
      view.attack_setting.valueChanged --> model.on_attack_changed
      view.decay_slider.valueChanged --> model.on_decay_changed
      view.decay_setting.valueChanged --> model.on_decay_changed
      view.sus_level_slider.valueChanged --> model.on_sus_level_changed
      view.sus_level_setting.valueChanged --> model.on_sus_level_changed
      view.sus_rate_slider.valueChanged --> model.on_sus_rate_changed
      view.sus_rate_setting.valueChanged --> model.on_sus_rate_changed
      view.tune_note.currentIndexChanged --> dashboard._on_tune_note_changed --> model.on_target_pitch_changed
      view.tune_octave.valueChanged --> dashboard._on_tune_note_changed --> model.on_target_pitch_changed
      view.apply_suggested_tune.released --> model.on_apply_suggested_tune_clicked
      view.tune_slider.valueChanged --> model.on_tune_changed
      view.tune_setting.editingFinished --> model.on_tune_changed
      view.subtune_slider.valueChanged --> model.on_subtune_changed
      view.subtune_setting.editingFinished --> model.on_subtune_changed
      view.brr_setting.editingFinished --> model.on_brr_setting_changed

Multisample
~~~~~~~~~~~

.. mermaid::

   flowchart LR
      view.multisample_sample_add.released --> dashboard.on_multisample_add_clicked --> model.on_multisample_add_clicked
      view.multisample_sample_remove.released --> model.multisample_sample_remove_clicked
      view.multisample_sample_name.editingFinished --> dashboard.multisample_sample_hanged --> model.on_multisample_changed
      view.multisample_sample_notes.editingFinished --> dashboard.multisample_sample_hanged --> model.on_multisample_changed
      view.multisample_sample_notehead.currentIndexChanged --> dashboard.multisample_sample_hanged --> model.on_multisample_changed
      view.multisample_sample_output.editingFinished --> dashboard.multisample_sample_hanged --> model.on_multisample_changed
      view.multisample_unmapped_list.doubleClicked --> dashboard._on_multisample_umapped_doubleclicked --> model.on_multisample_add_clicked

Global Settings
---------------

.. mermaid::

   flowchart LR
     view.global_volume_slider.valueChanged --> model.on_global_volume_changed
     view.global_volume_setting.textEdited --> model.on_global_volume_changed
     view.global_legato.stateChanged --> model.on_global_legato_changed
     view.echo_enable.stateChanged --> model.on_global_echo_en_changed
     view.echo_ch0.stateChanged --> model.on_echo_en_changed
     view.echo_ch1.stateChanged --> model.on_echo_en_changed
     view.echo_ch2.stateChanged --> model.on_echo_en_changed
     view.echo_ch3.stateChanged --> model.on_echo_en_changed
     view.echo_ch4.stateChanged --> model.on_echo_en_changed
     view.echo_ch5.stateChanged --> model.on_echo_en_changed
     view.echo_ch6.stateChanged --> model.on_echo_en_changed
     view.echo_ch7.stateChanged --> model.on_echo_en_changed
     view.echo_filter0.toggled --> model.on_filter_0_toggled
     view.echo_left_slider.toggled --> model.on_echo_left_changed
     view.echo_left_setting.editingFinished --> model.on_echo_left_changed
     view.echo_left_surround.stateChanged --> model.on_echo_left_surround_changed
     view.echo_right_slider.toggled --> model.on_echo_right_changed
     view.echo_right_setting.editingFinished --> model.on_echo_right_changed
     view.echo_right_surround.stateChanged --> model.on_echo_right_surround_changed
     view.echo_feedback_slider.toggled --> model.on_echo_feedback_changed
     view.echo_feedback_setting.editingFinished --> model.on_echo_feedback_changed
     view.echo_feedback_surround.stateChanged --> model.on_echo_feedback_surround_changed
     view.echo_delay_slider.valueChanged --> model.on_echo_delay_changed
     view.echo_delay_setting.valueChanged --> model.on_echo_delay_changed
     view.sample_opt_default.toggled --> model.on_sample_opt_selected
     view.sample_opt_optimized.toggled --> model.on_sample_opt_selected
     view.sample_opt_redux1.toggled --> model.on_sample_opt_selected
     view.sample_opt_redux2.toggled --> model.on_sample_opt_selected
     view.sample_opt_custom.toggled --> model.on_sample_opt_selected
     view.sample_opt_00.currentIndexChanged --> dashboard._on_sample_opt_source_changed --> model.on_sample_opt_source_changed
     view.sample_opt_01.currentIndexChanged --> dashboard._on_sample_opt_source_changed --> model.on_sample_opt_source_changed
     view.sample_opt_02.currentIndexChanged --> dashboard._on_sample_opt_source_changed --> model.on_sample_opt_source_changed
     view.sample_opt_03.currentIndexChanged --> dashboard._on_sample_opt_source_changed --> model.on_sample_opt_source_changed
     view.sample_opt_04.currentIndexChanged --> dashboard._on_sample_opt_source_changed --> model.on_sample_opt_source_changed
     view.sample_opt_05.currentIndexChanged --> dashboard._on_sample_opt_source_changed --> model.on_sample_opt_source_changed
     view.sample_opt_06.currentIndexChanged --> dashboard._on_sample_opt_source_changed --> model.on_sample_opt_source_changed
     view.sample_opt_07.currentIndexChanged --> dashboard._on_sample_opt_source_changed --> model.on_sample_opt_source_changed
     view.sample_opt_08.currentIndexChanged --> dashboard._on_sample_opt_source_changed --> model.on_sample_opt_source_changed
     view.sample_opt_09.currentIndexChanged --> dashboard._on_sample_opt_source_changed --> model.on_sample_opt_source_changed
     view.sample_opt_0a.currentIndexChanged --> dashboard._on_sample_opt_source_changed --> model.on_sample_opt_source_changed
     view.sample_opt_0b.currentIndexChanged --> dashboard._on_sample_opt_source_changed --> model.on_sample_opt_source_changed
     view.sample_opt_0c.currentIndexChanged --> dashboard._on_sample_opt_source_changed --> model.on_sample_opt_source_changed
     view.sample_opt_0d.currentIndexChanged --> dashboard._on_sample_opt_source_changed --> model.on_sample_opt_source_changed
     view.sample_opt_0e.currentIndexChanged --> dashboard._on_sample_opt_source_changed --> model.on_sample_opt_source_changed
     view.sample_opt_0f.currentIndexChanged --> dashboard._on_sample_opt_source_changed --> model.on_sample_opt_source_changed
     view.sample_opt_10.currentIndexChanged --> dashboard._on_sample_opt_source_changed --> model.on_sample_opt_source_changed
     view.sample_opt_11.currentIndexChanged --> dashboard._on_sample_opt_source_changed --> model.on_sample_opt_source_changed
     view.sample_opt_12.currentIndexChanged --> dashboard._on_sample_opt_source_changed --> model.on_sample_opt_source_changed
     view.sample_opt_13.currentIndexChanged --> dashboard._on_sample_opt_source_changed --> model.on_sample_opt_source_changed


Preferences Signal/Slot Map
===========================

.. mermaid::

   flowchart LR
     dialog.select_amk_fname.released --> dashboard.on_amk_select_clicked
     dialog.select_sample_pack_fname.released --> dashboard.on_select_sample_pack_fname_clicked
     dialog.select_spcplay.released --> dashboard.on_select_spcplay_clicked
     dialog.add_sample_pack.released --> dashboard.on_add_sample_pack_clicked
     dialog.remove_sample_pack.released --> dashboard.on_remove_sample_pack_clicked
