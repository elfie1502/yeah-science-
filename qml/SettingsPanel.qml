import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: settings
    objectName: "settingsPanel"
    anchors.centerIn: parent
    width: 460; height: 300
    modal: false; focus: true
    onOpened: station.stop()
    background: Panel {
        border.color: "#f3c623"
        border.width: 1
    }
    ColumnLayout {
        anchors.fill: parent; anchors.margins: 20; spacing: 12
        RowLayout {
            spacing: 8
            Rectangle {
                width: 24; height: 24; radius: 3
                color: "#1f2a37"
                border.color: "#f3c623"; border.width: 1
                Label { anchors.centerIn: parent; text: "N"; color: "#f3c623"; font.bold: true }
            }
            Label { text: "Session Operator Notes"; color: "#e2e8f0"; font.pixelSize: 20; font.bold: true }
        }
        Label {
            text: "Leave notes for your telemetry run. Typing text in input fields must NEVER transmit drive movement to the rover."
            color: "#8a99ad"
            wrapMode: Text.Wrap
            Layout.fillWidth: true
            font.pixelSize: 12
        }
        TextField {
            objectName: "noteInput"
            Layout.fillWidth: true
                    onActiveFocusChanged: {
            if (activeFocus) {
                station.clear_keyboard_input()  // Neutralize ongoing drive velocities during reports typing
            }
        }
        
        Keys.onPressed: (event) => {
            event.accepted = false  // Force the text component to process keystrokes natively
        }

            placeholderText: "What scenario or feature are you testing?"
            palette.base: "#0a0e13"
            palette.text: "#e2e8f0"
        }
        Label {
            text: "Endpoint: " + station.endpoint + "\nEdit config/local.json and restart to change ports."
            color: "#566b82"
            font.pixelSize: 11
            font.family: Qt.platform.os === "windows" ? "Consolas" : "monospace"
        }
        Item { Layout.fillHeight: true }
        Button {
            text: "Back to Station"
            Layout.alignment: Qt.AlignRight
            onClicked: settings.close()
        }
    }
}
