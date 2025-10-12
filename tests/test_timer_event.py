import threading
import time
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from timer_event import TimerEvent


class TimerEventTestCase(unittest.TestCase):
    def _wait_for(self, predicate, timeout=2.0, poll=0.01):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if predicate():
                return True
            time.sleep(poll)
        return False

    def test_timer_emits_monotonic_payloads(self):
        timer = TimerEvent(interval=0.05, name="test_timer")
        self.addCleanup(timer.stop)

        payloads = []
        done = threading.Event()

        def handler(packet):
            payloads.append(packet["payload"])
            if len(payloads) >= 5:
                done.set()

        timer.subscribe("collector", handler)

        self.assertTrue(done.wait(timeout=2), "Expected at least five timer ticks within 2s")
        self.assertGreaterEqual(len(payloads), 5)
        self.assertTrue(all(earlier <= later for earlier, later in zip(payloads, payloads[1:])))

    def test_pause_buffers_until_unpaused(self):
        timer = TimerEvent(interval=0.05, name="pause_test")
        self.addCleanup(timer.stop)

        payloads = []
        lock = threading.Lock()
        resumed = threading.Event()
        after_resume = threading.Event()
        before_pause = {"count": 0}

        def handler(packet):
            with lock:
                payloads.append(packet["payload"])
                if resumed.is_set() and len(payloads) >= before_pause["count"] + 3:
                    after_resume.set()

        timer.subscribe("listener", handler)

        # Wait for initial events to start flowing
        while True:
            with lock:
                if len(payloads) >= 2:
                    break
            time.sleep(0.01)

        with lock:
            before_pause["count"] = len(payloads)
        timer.pause()

        time.sleep(0.2)
        with lock:
            during_pause = len(payloads)
        self.assertEqual(before_pause["count"], during_pause, "No events should be delivered while paused")

        resumed.set()
        timer.unpause()
        self.assertTrue(after_resume.wait(timeout=2), "Buffered events should flush after unpause")
        with lock:
            self.assertGreaterEqual(len(payloads), before_pause["count"] + 3)

    def test_stop_is_idempotent(self):
        timer = TimerEvent(interval=0.05, name="stop_test")
        timer.stop()
        self.assertFalse(timer.is_alive())
        timer.stop()  # should not raise
        self.assertFalse(timer.is_alive())

    def test_timer_stop_without_wait(self):
        timer = TimerEvent(interval=0.05, name="stop_nowait")
        start = time.time()
        timer.stop(wait=False)
        self.assertLess(time.time() - start, 0.5)
        timer.join(timeout=1)
        self.assertFalse(timer.is_alive())

    def test_lazy_start_requires_manual_trigger(self):
        timer = TimerEvent(interval=0.05, name="lazy", auto_start=False)
        self.addCleanup(timer.stop)

        payloads = []

        timer.subscribe("collector", lambda packet: payloads.append(packet["payload"]))

        time.sleep(0.2)
        self.assertEqual(len(payloads), 0)

        timer.start_timer()
        self.assertTrue(self._wait_for(lambda: len(payloads) >= 3))

    def test_change_interval_applies(self):
        timer = TimerEvent(interval=0.05, name="change")
        self.addCleanup(timer.stop)

        timestamps = []
        lock = threading.Lock()
        finished = threading.Event()

        def handler(packet):
            with lock:
                timestamps.append(time.time())
                if len(timestamps) >= 8:
                    finished.set()

        timer.subscribe("collector", handler)

        self.assertTrue(self._wait_for(lambda: len(timestamps) >= 3))
        timer.change_interval(0.01, apply_immediately=True)
        self.assertTrue(finished.wait(timeout=2))

        with lock:
            first_gap = timestamps[1] - timestamps[0]
            post_change_gap = timestamps[-1] - timestamps[-2]
        self.assertLess(post_change_gap, first_gap * 0.8, "Interval should shorten after change")

    def test_context_manager_starts_and_stops_timer(self):
        payloads = []

        with TimerEvent(interval=0.05, name="ctx", auto_start=False) as timer:
            timer.subscribe("collector", lambda packet: payloads.append(packet["payload"]))
            self.assertTrue(self._wait_for(lambda: len(payloads) >= 2))

        self.assertFalse(timer.is_timer_running())
        self.assertFalse(timer.is_alive())


if __name__ == "__main__":
    unittest.main()
