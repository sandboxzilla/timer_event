import threading
import time
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from timer_event import EventThread


class EventThreadTestCase(unittest.TestCase):
    def test_post_delivers_packet(self):
        bus = EventThread("alerts")
        self.addCleanup(bus.stop)

        received = []
        done = threading.Event()

        def handler(packet):
            received.append(packet)
            done.set()

        handle = bus.subscribe("listener", handler)
        self.assertTrue(hasattr(handle, "unsubscribe"))
        bus.post({"msg": "ok"})

        self.assertTrue(done.wait(timeout=1), "Expected handler to fire within 1s")
        self.assertEqual(received[0]["payload"], {"msg": "ok"})
        self.assertEqual(received[0]["event"], "alerts")
        self.assertEqual(received[0]["dest"], "listener")

    def test_operator_overloads_add_and_remove(self):
        bus = EventThread("numbers")
        self.addCleanup(bus.stop)

        done = threading.Event()

        def handler(packet):
            done.set()

        bus += {"name": "adder", "on_event": handler}
        bus.post(42)

        self.assertTrue(done.wait(timeout=1))

        done.clear()
        bus -= "adder"
        bus.post(100)
        self.assertFalse(done.wait(timeout=0.2), "Handler should have been removed")

    def test_error_policy_continue_keeps_dispatching(self):
        bus = EventThread("errors", error_policy="continue")
        self.addCleanup(bus.stop)

        first = threading.Event()
        second = threading.Event()

        def failing(packet):
            first.set()
            raise RuntimeError("boom")

        def succeeding(packet):
            second.set()

        bus.subscribe("fails", failing)
        bus.subscribe("succeeds", succeeding)

        bus.post("payload")

        self.assertTrue(first.wait(timeout=1))
        self.assertTrue(second.wait(timeout=1), "Second handler should run despite failure in the first")

    def test_error_policy_stop_halts_dispatch(self):
        bus = EventThread("halt", error_policy="stop")
        self.addCleanup(bus.stop)

        calls = []
        done = threading.Event()

        def failing(packet):
            calls.append(packet["dest"])
            raise RuntimeError("fail hard")

        def succeeding(packet):
            calls.append(packet["dest"])
            done.set()

        bus.subscribe("fails", failing)
        bus.subscribe("succeeds", succeeding)
        bus.post("payload")

        time.sleep(0.2)
        self.assertIn("fails", calls)
        self.assertNotIn("succeeds", calls, "Dispatcher should stop before invoking subsequent handlers")
        self.assertFalse(bus.is_running)

    def test_drop_newest_overflow_policy_discards_latest(self):
        bus = EventThread("bounded", max_queue_size=1, overflow_policy="drop_newest")
        self.addCleanup(bus.stop)

        received = []
        done = threading.Event()

        def handler(packet):
            received.append(packet["payload"])
            if len(received) >= 2:
                done.set()

        bus.subscribe("collector", handler)
        bus.pause()

        bus.post(1)
        time.sleep(0.1)  # allow dispatcher to pick the first packet and block on pause
        bus.post(2)
        bus.post(3)  # should be dropped

        bus.unpause()
        self.assertTrue(done.wait(timeout=1))
        self.assertEqual(received, [1, 2])

    def test_subscription_handle_unsubscribe(self):
        bus = EventThread("handles")
        self.addCleanup(bus.stop)

        called = threading.Event()

        def handler(packet):
            called.set()

        handle = bus.subscribe("worker", handler)
        self.assertEqual(handle.name, "worker")
        self.assertTrue(handle.active)
        handle.unsubscribe()
        self.assertFalse(handle.active)
        bus.post("payload")
        self.assertFalse(called.wait(timeout=0.2))

    def test_duplicate_subscribe_raises(self):
        bus = EventThread("duplicates")
        self.addCleanup(bus.stop)

        bus.subscribe("worker", lambda packet: None)
        with self.assertRaises(ValueError):
            bus.subscribe("worker", lambda packet: None)

    def test_concurrent_subscribe_and_unsubscribe(self):
        processed = []
        lock = threading.Lock()
        errors = []

        def on_error(exc, subscriber, packet):
            errors.append((exc, subscriber))

        bus = EventThread("concurrency", on_error=on_error)
        self.addCleanup(bus.stop)

        def worker(worker_id):
            for i in range(20):
                name = f"w{worker_id}-{i}"
                delivered = threading.Event()

                def handler(packet, delivered=delivered, name=name):
                    with lock:
                        processed.append((name, packet["payload"]))
                    delivered.set()

                handle = bus.subscribe(name, handler)
                bus.post((worker_id, i))
                delivered.wait(timeout=1)
                handle.unsubscribe()

        threads = [threading.Thread(target=worker, args=(idx,)) for idx in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertFalse(errors)
        self.assertGreaterEqual(len(processed), 5 * 20)

    def test_queue_size_and_max_queue_size(self):
        bus = EventThread("buffer", max_queue_size=5, overflow_policy="block")
        self.addCleanup(bus.stop)

        blocker = threading.Event()
        started = threading.Event()

        def slow_handler(packet):
            started.set()
            blocker.wait(timeout=1)

        bus.subscribe("slow", slow_handler)
        bus.post(1)
        self.assertTrue(started.wait(timeout=1))

        bus.post(2)
        bus.post(3)
        time.sleep(0.05)
        self.assertEqual(bus.max_queue_size, 5)
        self.assertGreaterEqual(bus.queue_size, 2)

        blocker.set()
        time.sleep(0.1)

    def test_on_dispatch_hook_invoked(self):
        observed = []
        done = threading.Event()

        def on_dispatch(name, packet):
            observed.append((name, packet["payload"]))
            done.set()

        bus = EventThread("metrics", on_dispatch=on_dispatch)
        self.addCleanup(bus.stop)

        bus.subscribe("listener", lambda packet: None)
        bus.post("value")
        self.assertTrue(done.wait(timeout=1))
        self.assertEqual(observed, [("listener", "value")])

    def test_context_manager_auto_stop(self):
        with EventThread("ctx") as bus:
            bus.post("payload")
        self.assertFalse(bus.is_running)
        self.assertFalse(bus.is_alive())

    def test_stop_without_wait(self):
        bus = EventThread("nowait")
        start = time.time()
        bus.stop(wait=False)
        self.assertLess(time.time() - start, 0.5)
        bus.join(timeout=1)
        self.assertFalse(bus.is_alive())


if __name__ == "__main__":
    unittest.main()
