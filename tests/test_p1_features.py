
import unittest
import time
from threading import Event, Lock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from timer_event import EventThread, TimerEvent

class P1FeaturesTestCase(unittest.TestCase):
    def test_subscription_handle(self):
        bus = EventThread("handle_test")
        self.addCleanup(bus.stop)
        
        received = []
        done = Event()

        def handler(p):
            received.append(p["payload"])
            done.set()

        handle = bus.subscribe("sub1", handler)
        self.assertEqual(bus.subscriber_count, 1)
        
        bus.post(1)
        self.assertTrue(done.wait(timeout=1))
        self.assertEqual(received, [1])

        handle.unsubscribe()
        self.assertEqual(bus.subscriber_count, 0)
        
        bus.post(2)
        time.sleep(0.1) # Give time for potential dispatch
        self.assertEqual(received, [1], "Handler should not be called after unsubscribe via handle")

    def test_duplicate_subscriber_name_raises_error(self):
        bus = EventThread("duplicate_test")
        self.addCleanup(bus.stop)
        
        def handler(p):
            pass
            
        bus.subscribe("sub", handler)
        with self.assertRaises(ValueError):
            bus.subscribe("sub", handler)

    def test_context_manager_stops_thread(self):
        with EventThread("ctx_test") as bus:
            self.assertTrue(bus.is_running)
        self.assertFalse(bus.is_running)

    def test_timer_lazy_start(self):
        timer = TimerEvent(interval=0.1, auto_start=False)
        self.addCleanup(timer.stop)
        
        self.assertFalse(timer.is_timer_running())
        
        received = []
        done = Event()
        def handler(p):
            received.append(p)
            done.set()
        
        timer.subscribe("collector", handler)
        time.sleep(0.2)
        self.assertEqual(len(received), 0, "Timer should not fire before start")
        
        timer.start_timer()
        self.assertTrue(timer.is_timer_running())
        self.assertTrue(done.wait(timeout=1))
        self.assertGreaterEqual(len(received), 1)

    def test_timer_change_interval(self):
        timer = TimerEvent(interval=0.5, auto_start=False)
        self.addCleanup(timer.stop)
        
        payloads = []
        lock = Lock()
        
        def handler(p):
            with lock:
                payloads.append(p["payload"])

        timer.subscribe("collector", handler)
        timer.start_timer()
        
        time.sleep(0.6) # Should get 1 tick
        with lock:
            self.assertEqual(len(payloads), 1)
            
        timer.change_interval(0.1, apply_immediately=True)
        
        time.sleep(0.5) # Should get 1 immediate + 4-5 more
        with lock:
            self.assertGreaterEqual(len(payloads), 5)

    def test_metrics_properties(self):
        bus = EventThread("metrics", max_queue_size=5)
        self.addCleanup(bus.stop)
        
        self.assertEqual(bus.subscriber_count, 0)
        self.assertEqual(bus.queue_size, 0)
        self.assertEqual(bus.max_queue_size, 5)
        
        bus.subscribe("sub1", lambda p: None)
        self.assertEqual(bus.subscriber_count, 1)
        
        bus.pause()
        for i in range(3):
            bus.post(i)
            
        self.assertEqual(bus.queue_size, 3)
        bus.unpause()
        time.sleep(0.2)
        self.assertEqual(bus.queue_size, 0)

if __name__ == "__main__":
    unittest.main()
