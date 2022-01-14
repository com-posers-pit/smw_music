// SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
// <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
//
// SPDX-License-Identifier: AGPL-3.0-only

import MuseScore 3.0
import FileIO 3.0

MuseScore {
    version: "0.1.2"
    description: "MML"
    menuPath: "Plugins.MML"

    FileIO {
        id: mmlFile;
        source: "/tmp/score.mml"
    }

    FileIO {
        id: xmlFile;
        source: "/tmp/score.musicxml"
    }

    onRun: {
        const server = "http://localhost:5000/mml_uploader";

        // Write the score to a temporary file
        writeScore(curScore, xmlFile.source, "musicxml");

        // Create a new request
        const XHR = new XMLHttpRequest();
        const boundary = "kitties_are_so_nice";

        // Define the request payload
        var data = "";
        data += "--" + boundary + "\r\n";
        data += "content-disposition: form-data; ";
        data += 'name="file";';
        data += 'filename="score.musicxml"\r\n';
        data += "Content-Type: application/vnd.recordare.musicxml3+xml\r\n";
        data += "\r\n";
        data += xmlFile.read() + "\r\n";
        data += "--" + boundary + "--";

        // Define the statechange callback function (which writes the MML file)
        XHR.onreadystatechange = function() {
            if (XHR.readyState == XMLHttpRequest.DONE) {
                mmlFile.write(XHR.responseText);
            }
        }

        // Connect to the server
        XHR.open("POST", server);
        XHR.setRequestHeader("Content-Type",
            "multipart/form-data; boundary=" + boundary);
        XHR.send(data);
    }
}
