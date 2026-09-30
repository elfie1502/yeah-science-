import unittest
import time
from app.connection_monitor import ConnectionMonitor, ConnectionState

class TestConnectionStates(unittest.TestCase):
    def test_disconnected_initially(self):
        monitor = ConnectionMonitor()
        self.assertEqual(monitor.state, ConnectionState.DISCONNECTED)
    
    def test_waiting_after_connect(self):
        monitor = ConnectionMonitor()
        monitor.on_connect()
        self.assertEqual(monitor.state, ConnectionState.WAITING)
    
    def test_live_after_valid_telemetry(self):
        monitor = ConnectionMonitor()
        monitor.on_connect()
        monitor.on_telemetry_received(b"valid_packet_data")
        self.assertEqual(monitor.state, ConnectionState.LIVE)
    
    def test_stale_after_timeout(self):
        monitor = ConnectionMonitor(stale_after_ms=100)
        monitor.on_connect()
        monitor.on_telemetry_received(b"valid_packet_data")
        time.sleep(0.15)
        monitor.update()
        self.assertEqual(monitor.state, ConnectionState.STALE)
    
    def test_invalid_bytes_ignored(self):
        monitor = ConnectionMonitor()
        monitor.on_connect()
        monitor.on_telemetry_received(b"garbage_stream")
        self.assertEqual(monitor.state, ConnectionState.WAITING)

if __name__ == "__main__":
    unittest.main()
