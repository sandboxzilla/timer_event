#
#  Copyright (c) 2021.  SandboxZilla
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this
#  software and associated documentation files (the "Software"), to deal in the Software
#  without restriction, including without limitation the rights to use, copy, modify,
#  merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
#  permit persons to whom the Software is furnished to do so.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
#  INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
#  PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#  HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
#  OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#
import time
import os
import inspect
import unittest

currentdir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir) + '/src'
os.sys.path.insert(0, parentdir)
parentdir = parentdir + '/timer_event'
os.sys.path.insert(0, parentdir)


from timer_event import TimerEvent

class TestTimerEvent(unittest.TestCase):
    """
    This class contains unit tests for the TimerEvent class. The tests include testing the creation of a TimerEvent object,
    subscribing to timers, triggering timers at the expected interval, and stopping the timer. The tests use a helper
    function to assert that the payload received by the subscriber's callback function is equal to the expected payload.
    """

    def test_timer(self):
        """
        Test the TimerEvent class by creating a TimerEvent object with a 1 second interval, subscribing to two timers, and
        asserting that the timers are triggered at approximately the expected time. The test uses a helper function to assert
        that the payload received by the subscriber's callback function is equal to the expected payload.
        """
        global NOW1
        global NOW2
        NOW1 = 0.0
        NOW2 = 0.0

        def on_event(packet):
            global NOW1
            global NOW2
            name = packet["dest"]
            if name == "timer1":
                NOW1 = time.time()
            elif name == "timer2":
                NOW2 = time.time()

        te = TimerEvent(interval=1.0, name="test_timer")
        te.subscribe(name="timer1", on_event=on_event)
        te.subscribe(name="timer2", on_event=on_event)
        then = time.time()
        count = 0
        while NOW1 == 0.0 or NOW2 == 0.0:
            time.sleep(0.5)
            if count > 6:
                break
            count += 1
        self.assertAlmostEqual(abs(NOW1 - then), 1.0, delta=1.00001)
        self.assertAlmostEqual(abs(NOW2 - then), 1.0, delta=1.00001)
        self.assertAlmostEqual(abs(NOW1 - NOW2), 0.0, delta=0.00001)
        te.stop()

    def test_pause(self):
        """
        Test the pausing and unpasing of a TimerEvent object. The test creates a TimerEvent object with a 1 second interval, pauses the event postings,
        and asserts that the timer is no longer posting.  Than unpauses and asserts that it;s posting again.
        """
        global NOW
        NOW = 0.0

        def on_event(packet):
            global NOW
            NOW = packet["payload"]

        te = TimerEvent(interval=1.0, name="test_pause")
        te.subscribe(name="timer1", on_event=on_event)
        time.time()
        stop = time.time() + 15
        now = 0.0
        start = 0.0
        while now < stop:
            # sync the two threads
            # tight loop until NOW has a legit time
            if NOW == 0.0:
                continue
            elif start == 0.0:
                start = time.time()
                time.sleep(0.25)
                now = time.time()
                self.assertAlmostEqual(
                    abs(NOW - start), 0.0, delta=1.059)
                self.assertAlmostEqual(
                    abs(NOW - now), 0.25, delta=1.059)
            else:
                now = time.time()
                time.sleep(0.1)
                if 5.0 <= (now-start) < 5.2:
                    self.assertAlmostEqual(
                        abs(NOW - now), 0.0, delta=1.001)
                    te.pause()
                elif 8.0 <= (now-start) < 8.2:
                    self.assertAlmostEqual(
                        abs(NOW - now), 4.0, delta=1.001)
                    te.unpause()
                elif 10.0 <= (now-start) < 10.5:
                    self.assertAlmostEqual(
                        abs(NOW - now), 0.0, delta=1.001)
                    break

        te.stop()

    def test_stop(self):
        """
        Test the stopping of a TimerEvent object. The test creates a TimerEvent object with a 1 second interval, stops the timer,
        and asserts that the timer is no longer running.
        """
        te = TimerEvent(1.0)
        te.stop()
        self.assertFalse(te.is_alive())


if __name__ == '__main__':
    unittest.main()
