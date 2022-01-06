#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

from flask import Flask, make_response, render_template, request
from werkzeug.utils import secure_filename

from smw_music import music_xml

application = Flask(__name__)


@application.route("/upload")
def upload_file():
    return render_template("upload.html")


@application.route("/uploader", methods=["GET", "POST"])
def uploader():
    if request.method == "POST":
        try:
            f = request.files["file"]
            fname = f"/tmp/{secure_filename(f.filename)}"
            f.save(fname)
            song = music_xml.Song.from_music_xml(fname)
            response = make_response(song.amk, 200)
        except Exception as e:
            response = make_response(str(e), 400)

        response.mimetype = "text/plain"
        return response


if __name__ == "__main__":
    application.run(debug=True)
