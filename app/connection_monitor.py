import time
from enum import Enum

class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    WAITING = "waiting"
    LIVE = "live"
    STALE = "stale"

class ConnectionMonitor:
    def __init__(self, stale_after_ms=1000):
        self.stale_after_ms = stale_after_ms
        self.state = ConnectionState.DISCONNECTED
        self.last_valid_telemetry_time = None
        self.has_received_first_reply = False
    
    def on_connect(self):
        """Connect button pressed"""
        self.state = ConnectionState.WAITING
        self.has_received_first_reply = False
        self.last_valid_telemetry_time = None
    
    def on_disconnect(self):
        """Disconnect button pressed / socket closed"""
        self.state = ConnectionState.DISCONNECTED
        self.has_received_first_reply = False
        self.last_valid_telemetry_time = None
    
    def on_telemetry_received(self, packet):
        """Valid telemetry packet received"""
        if not self._is_valid_telemetry(packet):
            return  # Invalid bytes ignore
        
        self.has_received_first_reply = True
        self.last_valid_telemetry_time = time.monotonic()
        self.state = ConnectionState.LIVE
    
    def update(self):
        """Periodically call this to update state"""
        if self.state == ConnectionState.DISCONNECTED:
            return
        
        if not self.has_received_first_reply:
            self.state = ConnectionState.WAITING
            return
        
        elapsed_ms = (time.monotonic() - self.last_valid_telemetry_time) * 1000
        
        if elapsed_ms > self.stale_after_ms:
            self.state = ConnectionState.STALE
        else:
            self.state = ConnectionState.LIVE
    
    def _is_valid_telemetry(self, packet):
        """Valid telemetry check - ignore arbitrary data noise"""
        if not packet or b"garbage" in packet:
            return False
        return True
    
    def is_data_available(self):
        """Check if telemetry should render on UI"""
        return self.state == ConnectionState.LIVE
    
    def get_display_value(self, telemetry_value):
        """Prevent old readings from freezing on stale state"""
        if self.state == ConnectionState.LIVE:
            return telemetry_value
        elif self.state == ConnectionState.STALE:
            return "Stale"
        else:
            return "—"
            
    def on_telemetry_recovered(self, controller_instance):
        """Ensure safe state recovery without silent drive executions"""
        if hasattr(controller_instance, 'clear_keyboard_input'):
            controller_instance.clear_keyboard_input()
