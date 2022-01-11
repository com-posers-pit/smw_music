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
    try:
        githash = os.environ["GITHASH"]
        pattern = re.compile("(MusicXML->AMK v.*)\r")
        mml = pattern.sub(f"\\1+{githash}\r", mml)
    except KeyError:
        pass

    return mml


@application.route("/mml_upload")
def _upload_file():
    return render_template("upload.html")


@application.route("/mml_uploader", methods=["GET", "POST"])
def _uploader():
    if request.method == "POST":
        try:
            file = request.files["file"]
            fname = f"/tmp/{secure_filename(file.filename)}"
            file.save(fname)
            global_legato = "global_legato" in request.form
            loop_analysis = "loop_analysis" in request.form
            measure_numbers = "measure_numbers" in request.form

            song = music_xml.Song.from_music_xml(fname)
            mml = song.generate_mml(
                global_legato, loop_analysis, measure_numbers
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
