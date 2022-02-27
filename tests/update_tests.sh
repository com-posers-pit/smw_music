#!/bin/bash
# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: CC0-1.0

# This script updates all the test output files.  You shouldn't normally
# run it unless you're messing around with the MML headers, which affect
# all the tests.

smw_music_xml_to_mml "src/Articulations.mxl" "dst/Articulations.txt" --disable_dt
smw_music_xml_to_mml "src/Crescendos.mxl" "dst/Crescendos.txt" --disable_dt
smw_music_xml_to_mml "src/Crescendo_Triplet_Loops.mxl" "dst/Crescendo_Triplet_Loops.txt" --disable_dt --loop_analysis
smw_music_xml_to_mml "src/Dots.mxl" "dst/Dots.txt" --disable_dt
smw_music_xml_to_mml "src/Dynamics.mxl" "dst/Dynamics.txt" --disable_dt
smw_music_xml_to_mml "src/Empty_Section.mxl" "dst/Empty_Section.txt" --disable_dt --loop_analysis
smw_music_xml_to_mml "src/EndingTriplet.mxl" "dst/EndingTriplet.txt" --disable_dt
smw_music_xml_to_mml "src/ExtraInstruments.mxl" "dst/ExtraInstruments.txt" --disable_dt
smw_music_xml_to_mml "src/Grace_Notes.mxl" "dst/Grace_Notes.txt" --disable_dt
smw_music_xml_to_mml "src/Headers.mxl" "dst/Headers.txt" --disable_dt
smw_music_xml_to_mml "src/Instruments.mxl" "dst/Instruments_parse_to.txt" --disable_dt
smw_music_xml_to_mml "src/Loop_Point.mxl" "dst/Loop_Point.txt" --disable_dt
smw_music_xml_to_mml "src/Loops.mxl" "dst/Loops.txt" --loop_analysis --disable_dt
smw_music_xml_to_mml "src/Percussion.mxl" "dst/Percussion.txt" --disable_dt
smw_music_xml_to_mml "src/Percussion.mxl" "dst/Percussion_opt.txt" --disable_dt --optimize_percussion
smw_music_xml_to_mml "src/Pickup_Measure.mxl" "dst/Pickup_Measure.txt" --measure_numbers --disable_dt
smw_music_xml_to_mml "src/Repeats.mxl" "dst/Repeats.txt" --loop_analysis --disable_dt
smw_music_xml_to_mml "src/Slurs.mxl" "dst/Slurs.txt" --disable_dt
smw_music_xml_to_mml "src/SMB_Castle_Theme.mxl" "dst/SMB_Castle_Theme.txt" --disable_dt
smw_music_xml_to_mml "src/SwapRepeatAnnotation.mxl" "dst/SwapRepeatAnnotation.txt" --disable_dt
smw_music_xml_to_mml "src/Tempos.mxl" "dst/Tempos.txt" --disable_dt
smw_music_xml_to_mml "src/TiedArticulations.mxl" "dst/TiedArticulations.txt" --disable_dt
smw_music_xml_to_mml "src/Ties.mxl" "dst/Ties.txt" --disable_dt
smw_music_xml_to_mml "src/Triplets.mxl" "dst/Triplets.txt" --disable_dt
smw_music_xml_to_mml "src/SMB_Castle_Theme.musicxml" "dst/SMB_Castle_Theme.txt" --disable_dt
smw_music_xml_to_mml "src/SMB_Castle_Theme.musicxml" "dst/SMB_Castle_Theme_full.txt" --disable_dt --loop_analysis --optimize_percussion --measure_numbers
smw_music_xml_to_mml "src/SMB_Castle_Theme.musicxml" "dst/SMB_Castle_Theme_measures.txt" --measure_numbers --disable_dt
smw_music_xml_to_mml "src/SMB_Castle_Theme.musicxml" "dst/SMB_Castle_Theme_Echo.txt" --disable_dt --echo 2,3,4,0.109,Y,0.189,N,11,0.323,N,1
smw_music_xml_to_mml "src/SMB_Castle_Theme.musicxml" "dst/SMB_Castle_Theme_custom_samples.txt" --custom_samples --disable_dt
smw_music_xml_to_mml "src/Metadata.mxl" "dst/Metadata.txt" --disable_dt
smw_music_xml_to_mml "src/No_Metadata.mxl" "dst/No_Metadata.txt" --disable_dt
smw_music_xml_to_mml "src/Vibrato.mxl" "dst/Vibrato.txt" --disable_dt

smw_music_xml_to_mml "src/GUI_Test.mxl" "dst/ui/global_legato.mml" --disable_dt
smw_music_xml_to_mml "src/GUI_Test.mxl" "dst/ui/vanilla.mml" --disable_global_legato --disable_dt
smw_music_xml_to_mml "src/GUI_Test.mxl" "dst/ui/loop.mml" --disable_dt --disable_global_legato --loop_analysis
smw_music_xml_to_mml "src/GUI_Test.mxl" "dst/ui/measure_numbers.mml" --disable_dt --disable_global_legato --measure_numbers
smw_music_xml_to_mml "src/GUI_Test.mxl" "dst/ui/custom_samples.mml" --disable_dt --disable_global_legato --custom_samples
smw_music_xml_to_mml "src/GUI_Test.mxl" "dst/ui/custom_percussion.mml" --disable_dt --disable_global_legato --optimize_percussion
