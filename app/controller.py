"""Station coordinator. Input, transport and display state meet here.

This class has grown with the UI; there is room to separate responsibilities
when someone next changes it. Keep the mouse controls working while doing so.
"""
import logging
import math
import time

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot

from app.telemetry import TelemetryStore
from link.packets import decode, encode
from link.udp import UdpLink

log = logging.getLogger("station")


class Station(QObject):
    changed = Signal()
    eventsChanged = Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.link = UdpLink(config["station_port"], config["rover_port"])
        self.telemetry = TelemetryStore()
        self._online = False
        self._armed = False
        self._left = self._right = 0.0
        self._speed = config["drive_speed"]
        self._seq = 0
        self._events = []
                # Dictionary to track active telemetry keystrokes
        self.keyboard_inputs = {
            "forward": False,
            "reverse": False,
            "left": False,
            "right": False
        }
        self.selected_speed = self.config.get("drive_speed", 0.5)  # Fetch baseline configuration speed modifier

        self._invalid = 0
        self._timer = QTimer(self)
        self._timer.setInterval(config["send_period_ms"])
        self._timer.timeout.connect(self.tick)
        self._timer.start()
        self.note("Station ready. Start the simulator, then connect.")
        

    connected = Property(bool, lambda self: self._online, notify=changed)
    armed = Property(bool, lambda self: self._armed, notify=changed)
    telemetryData = Property("QVariantMap", lambda self: self.telemetry.values, notify=changed)
    eventLines = Property("QStringList", lambda self: self._events, notify=eventsChanged)
    speed = Property(float, lambda self: self._speed, notify=changed)
    leftCommand = Property(float, lambda self: self._left, notify=changed)
    rightCommand = Property(float, lambda self: self._right, notify=changed)
    rxBytes = Property(int, lambda self: self.link.rx, notify=changed)
    txBytes = Property(int, lambda self: self.link.tx, notify=changed)
    invalidPackets = Property(int, lambda self: self._invalid, notify=changed)
    endpoint = Property(str, lambda self: f"127.0.0.1:{self.config['rover_port']}", constant=True)

    def note(self, message, warning=False):
        (log.warning if warning else log.info)(message)
        self._events = (self._events + [time.strftime("%H:%M:%S") + "  " + message])[-80:]
        self.eventsChanged.emit()

    @Slot()
    def connectLink(self):
        if self._online:
            return
        try:
            self.link.open()
            self._online = True
            self.link.send(encode("hello", self._seq))
            self._seq += 1
            self.note("Datalink opened on port " + str(self.config["station_port"]))
        except OSError as exc:
            self.link.close()
            self._online = False
            self.note("Cannot open link: " + str(exc), True)
        self.changed.emit()

    @Slot()
    def disconnectLink(self):
        self.stop()
        self._armed = False
        self.link.close()
        self._online = False
        self.note("Datalink closed")
        self.changed.emit()

    @Slot()
    def toggleArm(self):
        if not self._online:
            self.note("Connect before enabling drive", True)
            return
        self.stop()
        self._armed = not self._armed
        self.note("Drive enabled" if self._armed else "Drive disabled")
        self.changed.emit()

    @Slot(float)
    def setSpeed(self, value):
        if math.isfinite(value):
            self._speed = max(0.1, min(1.0, value))
            self.changed.emit()

    @Slot(float, float)
    def setDrive(self, left, right):
        if not self._armed or not self._online:
            return
        if not (math.isfinite(left) and math.isfinite(right)):
            return
        self._left = max(-1.0, min(1.0, left)) * self._speed
        self._right = max(-1.0, min(1.0, right)) * self._speed
        self._send_drive()
        self.changed.emit()

    def _send_drive(self):
        if not self._online:
            return
        try:
            self.link.send(encode("drive", self._seq, left=self._left, right=self._right))
            self._seq += 1
        except OSError as exc:
            self.note("Send failed: " + str(exc), True)
            self._left = self._right = 0.0
            self._armed = False
            self.link.close()
            self._online = False

    @Slot()
    def stop(self):
        self._left = self._right = 0.0
        self._send_drive()
        self.changed.emit()

    @Slot()
    def tick(self):
        if self._online:
            try:
                packets = self.link.receive()
            except OSError as exc:
                self.note("Receive failed: " + str(exc), True)
                self.disconnectLink()
                return
            for raw in packets:
                try:
                    packet = decode(raw)
                except ValueError:
                    self._invalid += 1
                    if self._invalid == 1 or self._invalid % 20 == 0:
                        self.note(f"Dropped malformed packet (total {self._invalid})", True)
                    continue
                if packet["type"] == "telemetry":
                    first = self.telemetry.received_at is None
                    self.telemetry.update(packet)
                    if first:
                        self.note("First rover telemetry received")
            if self._armed:
                self._send_drive()
        self.changed.emit()

    @Slot()
    def clearEvents(self):
        self._events = []
        self.eventsChanged.emit()

    @Slot()
    def shutdown(self):
        self._timer.stop()
        self.disconnectLink()        

    @Slot(str, bool)
    def setKeyboardInput(self, direction, pressed):
        """Update the active keyboard input state maps from QML events"""
        if not hasattr(self, 'keyboard_inputs'):
            self.keyboard_inputs = {"forward": False, "reverse": False, "left": False, "right": False}
            self.selected_speed = self.config.get("drive_speed", 0.5)

        self.keyboard_inputs[direction] = pressed
        
        # Read active keys
        forward = self.keyboard_inputs["forward"]
        reverse = self.keyboard_inputs["reverse"]
        left = self.keyboard_inputs["left"]
        right = self.keyboard_inputs["right"]
        
        # Opposing vectors neutralize each other safely
        if forward and reverse: forward = reverse = False
        if left and right: left = right = False
        
        # Determine speed and turn vectors
        speed = self.selected_speed if forward else (-self.selected_speed if reverse else 0.0)
        turn = -1.0 if left else (1.0 if right else 0.0)
        
        # Send the final values to the motor driver
        self.setDrive(speed, turn)

    @Slot()
    def clear_keyboard_input(self):
        """Emergency safe stop routing to wipe all direction indexes"""
        self.keyboard_inputs = {"forward": False, "reverse": False, "left": False, "right": False}
        self.setDrive(0.0, 0.0)
