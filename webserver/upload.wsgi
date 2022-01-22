#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

import re
import os

from flask import Flask, make_response, render_template, request, send_file
from werkzeug.utils import secure_filename

from smw_music import music_xml

application = Flask(__name__)


def _update(mml: str) -> str:
    if githash := os.environ.get("GITHASH", ""):
        githash = os.environ["GITHASH"]
        pattern = re.compile("(MusicXML->AMK v.*)\r")
        mml = pattern.sub(f"\\1+{githash}\r", mml)

    return mml


@application.route("/mml_upload")
def _upload_file():
    return render_template("upload.html")


@application.route("/mml_uploader", methods=["GET", "POST"])
def _uploader():
    response = make_response(":-P", 400)
    if request.method == "POST":
        try:
            file = request.files["file"]
            fname = f"/tmp/{secure_filename(file.filename)}"
            file.save(fname)
            global_legato = "global_legato" in request.form
            loop_analysis = "loop_analysis" in request.form
            superloop_analysis = "superloop_analysis" in request.form
            measure_numbers = "measure_numbers" in request.form
            instrument_to_annotations = (
                "instrument_to_annotations" in request.form
            )
            echo_en = "echo_enabled" in request.form
            single_volumes = "single_volumes" in request.form
            custom_samples = "custom_samples" in request.form
            optimize_percussion = "optimize_percussion" in request.form

            if echo_en:
                channels = set()
                for chan in range(8):
                    if f"echo_ch{chan}" in request.form:
                        channels.add(chan)
                lvol = float(request.form["echo_lvol"]) / 100
                rvol = float(request.form["echo_rvol"]) / 100
                lvol_inv = "echo_lvol_inv" in request.form
                rvol_inv = "echo_rvol_inv" in request.form
                delay = int(request.form["echo_delay"])
                feedback = float(request.form["echo_fb"]) / 100
                fb_inv = "echo_fb_inv" in request.form
                filt = int(request.form["echo_filter"])

                echo_config = music_xml.EchoConfig(
                    channels,
                    (lvol, rvol),
                    (lvol_inv, rvol_inv),
                    delay,
                    feedback,
                    fb_inv,
                    filt,
                )
            else:
                echo_config = None

            song = music_xml.Song.from_music_xml(fname)
            mml = song.generate_mml(
                global_legato,
                loop_analysis,
                superloop_analysis,
                measure_numbers,
                True,  # Always emit datetime in prod
                echo_config,
                instrument_to_annotations,
                single_volumes,
                custom_samples,
                optimize_percussion,
            )
            mml = _update(mml)

            if "download_file" in request.form:
                fname += ".txt"
                with open(fname, "w", encoding="ascii") as fobj:
                    fobj.write(mml)
                response = send_file(fname, as_attachment=True)
            else:
                response = make_response(mml, 200)
                response.mimetype = "text/plain"
        except Exception as e:
            response = make_response(str(e), 400)
            response.mimetype = "text/plain"

    return response


if __name__ == "__main__":
    application.run(debug=True)
