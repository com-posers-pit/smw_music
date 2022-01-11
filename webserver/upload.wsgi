#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

from flask import Flask, make_response, render_template, request, send_file
from werkzeug.utils import secure_filename

from smw_music import music_xml

application = Flask(__name__)


@application.route("/mml_upload")
def _upload_file():
    return render_template("upload.html")


@application.route("/mml_uploader", methods=["GET", "POST"])
def _uploader():
    if request.method == "POST":
        try:
            f = request.files["file"]
            fname = f"/tmp/{secure_filename(f.filename)}"
            f.save(fname)
            global_legato = "global_legato" in request.form
            loop_analysis = "loop_analysis" in request.form
            measure_numbers = "measure_numbers" in request.form

            song = music_xml.Song.from_music_xml(fname)

            if "download_file" in request.form:
                fname += ".txt"
                song.to_mml_file(
                    fname, global_legato, loop_analysis, measure_numbers
                )
                response = send_file(fname, as_attachment=True)
            else:
                mml = song.generate_mml(
                    global_legato, loop_analysis, measure_numbers
                )
                response = make_response(mml, 200)
                response.mimetype = "text/plain"
        except Exception as e:
            response = make_response(str(e), 400)
            response.mimetype = "text/plain"

        return response


if __name__ == "__main__":
    application.run(debug=True)
