// SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
// <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
//
// SPDX-License-Identifier: AGPL-3.0-only

import MuseScore 3.0
import FileIO 3.0
import QtQuick 2.2
import QtQuick.Dialogs 1.2
import QtQuick.Controls 2.0
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.0

MuseScore {
  version: "0.1.2"
  description: "Convert score to MML via webservice"
  menuPath: "Plugins.MML"
  pluginType: "dock"
  dockArea: "right"
  width: 200
  height: 500

  ColumnLayout {
    spacing: 0
    Layout.fillWidth: false

    RowLayout {
      Text {
        text: "Server:"
      }
      TextField {
        id: "serverField"
      }
    }

    RowLayout {
      Button {
        id: "chooseOutput"
        text: "MML Output File"
        onClicked: fileDialog.open()
      }

      Text {
        id: "mmlPath"
        text: ""
      }
    }

    CheckBox {
      id: "globalLegato"
      text: qsTr("Enable Global Legato")
    }

    CheckBox {
      id: "measureNumbers"
      text: qsTr("Include Measure Numbers")
    }

    CheckBox {
      id: "loopAnalysis"
      text: qsTr("Perform Loop Analysis")
    }

    CheckBox {
      id: "superloopAnalysis"
      text: qsTr("Perform Superloop Analysis")
    }

    CheckBox {
      id: "echoEnabled"
      text: qsTr("Enable Echo")
    }

    RowLayout {
      Label {
        text: "Echo Channels"
      }

      CheckBox {
        id: "echo_ch0"
        text: "0"
      }
      CheckBox {
        id: "echo_ch1"
        text: "1"
      }
      CheckBox {
        id: "echo_ch2"
        text: "2"
      }
      CheckBox {
        id: "echo_ch3"
        text: "3"
      }
      CheckBox {
        id: "echo_ch4"
        text: "4"
      }
      CheckBox {
        id: "echo_ch5"
        text: "5"
      }
      CheckBox {
        id: "echo_ch6"
        text: "6"
      }
      CheckBox {
        id: "echo_ch7"
        text: "7"
      }
    }

    RowLayout {
      Label {
        text: "Left Vol"
      }

      Slider {
        id: "echoLvolSlider"
        from: 0
        to: 127
        stepSize: 1
        value: 50
        onMoved: echoLvolLabel.text = value
      }

      Label {
        id: "echoLvolLabel"
        text: "50"
      }

      CheckBox {
        id: "echoLvolInv"
        text: "Surround?"
      }
    }

    RowLayout {
      Label {
        text: "Right Vol"
      }

      Slider {
        id: "echoRvolSlider"
        from: 0
        to: 127
        stepSize: 1
        value: 50
        onMoved: echoRvolLabel.text = value
      }

      Label {
        id: "echoRvolLabel"
        text: "50"
      }

      CheckBox {
        id: "echoRvolInv"
        text: "Surround?"
      }
    }

    RowLayout {
      Label {
        text: "Room Size"
      }

      Slider {
        id: "echoDelaySlider"
        from: 0
        to: 15
        stepSize: 1
        value: 0
        onMoved: echoDelayLabel.text = 16*value + 'ms'
      }

      Label {
        id: "echoDelayLabel"
        text: "0ms"
      }
    }

    RowLayout {
      Label {
        text: "Fadeout"
      }

      Slider {
        id: "echoReverbSlider"
        from: 0
        to: 127
        stepSize: 1
        value: 50
        onMoved: echoReverbLabel.text = value
      }

      Label {
        id: "echoReverbLabel"
        text: "50"
      }

      CheckBox {
        id: "echoReverbInv"
        text: "Surround?"
      }
    }

    RowLayout {
      Label {
        text: "FIR Filter"
      }

      RadioButton {
        text: "0"
      }
      RadioButton {
        id: "filterFir1"
        checked: True
        text: "1"
      }
    }

    Button {
      id: "convertBtn"
      text: "Convert"
      onClicked: convert()
    }
  }


  //Dialogs
  FileDialog {
    id: fileDialog
    selectExisting: false
    title: "Export Location"
    onAccepted: {
      var path = fileDialog.fileUrl.toString();
      var os = Qt.platform.os;
      var unixPath = (os === "linux") || (os === "osx");

      // This is legit ridiculous.  url types apparently have to have the
      // 'file://' stripped out.  If we're on windows, there's an extra '/'
      // that needs to get yoinked too.
      path = path.substring("file://".length, path.length);
      if (!unixPath) {
        path = path.substring(1, path.length);
      }

      mmlPath.text = path;
    }
  }

  FileIO {
    id: mmlFile;
    source: ""
  }

  FileIO {
    id: xmlFile;
    source: tempPath() + "/score.musicxml"
  }

  MessageDialog {
    id: responseDlg
    visible: false
    function openErrorDialog(message) {
      title = qsTr("Error")
      text = "MML Conversion Error: " + message;
      open();
    }
    function openSuccessDialog() {
      title = qsTr("Success");
      text = "MML Conversion: Done";
      open();
    }
  }

  function convert() {
    const server = serverField.text;

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

    var options = [[globalLegato, "global_legato"],
                   [loopAnalysis, "loop_analysis"],
                   [superloopAnalysis, "superloop_analysis"],
                   [measureNumbers, "measure_numbers"],
                   [echoEnabled, "echo_enabled"],
                   [echo_ch0, "echo_ch0"],
                   [echo_ch1, "echo_ch1"],
                   [echo_ch2, "echo_ch2"],
                   [echo_ch3, "echo_ch3"],
                   [echo_ch4, "echo_ch4"],
                   [echo_ch5, "echo_ch5"],
                   [echo_ch6, "echo_ch6"],
                   [echo_ch7, "echo_ch7"],
                   [echoLvolInv, "echo_lvol_inv"],
                   [echoRvolInv, "echo_rvol_inv"],
                   [echoReverbInv, "echo_rev_inv"]];

     for (var i = 0; i < options.length; i++) {
       var checkbox = options[i][0];
       var label = options[i][1];
       if (checkbox.checked) {
         data += "--" + boundary + "\r\n";
         data += "content-disposition: form-data;"
         data += 'name="' + label + '"\r\n';
         data += "\r\n";
         data += '"1"\r\n';
       }
    }

    var options = [[echoLvolSlider, "echo_lvol"],
                   [echoRvolSlider, "echo_rvol"],
                   [echoDelaySlider, "echo_delay"],
                   [echoReverbSlider, "echo_reverb"]];

     for (var i = 0; i < options.length; i++) {
       var slider = options[i][0];
       var label = options[i][1];
       data += "--" + boundary + "\r\n";
       data += "content-disposition: form-data;"
       data += 'name="' + label + '"\r\n';
       data += "\r\n";
       data += '' + slider.value + '\r\n';
    }

    data += "--" + boundary + "\r\n";
    data += "content-disposition: form-data;"
    data += 'name="' + "echo_filter" + '"\r\n';
    data += "\r\n";
    data += '' + (filterFir1.checked ? "1" : "0") + '\r\n';

    data += "--" + boundary + "--";

    mmlFile.source = mmlPath.text

    // Define the statechange callback function (which writes the MML file or
    // dumps an error)
    XHR.onreadystatechange = function() {
      if (XHR.readyState == XMLHttpRequest.DONE) {
        if (XHR.status == 200) {
          mmlFile.write(XHR.responseText);
          responseDlg.openSuccessDialog();
        } else {
          responseDlg.openErrorDialog(XHR.responseText);
        }
      }
    }

    // Connect to the server
    XHR.open("POST", server);
    XHR.setRequestHeader("Content-Type",
        "multipart/form-data; boundary=" + boundary);
    XHR.send(data);
  }
}
