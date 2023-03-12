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
import os
import inspect
import unittest

currentdir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir) + '/src'
os.sys.path.insert(0, parentdir)

from timer_event.event import Event


class TestEvent(unittest.TestCase):
    """
    This class contains unit tests for the Event class. The tests include testing the subscription and unsubscription of
    subscribers, posting events with payloads, and adding and removing subscribers using the += and -= operators.
    """

    def test_subscribe(self):
        """
        Test the subscription of a subscriber to an event. The test creates an Event object, adds a subscriber with a callback
        function, posts an event with a payload, and then removes the subscriber. The test asserts that the payload received by
        the subscriber's callback function is equal to the expected payload.
        """
        event = Event("test_event")

        def on_event(payload):
            """
            A helper function used in the TimerEvent tests to assert that the payload received by the subscriber's callback function
            is equal to the expected payload.
            """
            self.assertEqual(payload, "test_payload")
        event.subscribe("test_subscriber", on_event)
        event.post("test_payload")
        event.unsubscribe("test_subscriber")

    def test_post(self):
        """
        Test the posting of an event with a payload to an event. The test creates an Event object, adds a subscriber with a
        callback function, posts an event with a payload, and then removes the subscriber. The test asserts that the payload
        received by the subscriber's callback function is equal to the expected payload.
        """
        event = Event("test_event")

        def on_event(payload):
            """
            A helper function used in the TimerEvent tests to assert that the payload received by the subscriber's callback function
            is equal to the expected payload.
            """
            self.assertEqual(payload, "test_payload")
        event.subscribe("test_subscriber", on_event)
        event.post("test_payload")
        event.unsubscribe("test_subscriber")

    def test_iadd(self):
        """
        Test the addition of a subscriber to an event using the += operator. The test creates an Event object, adds a subscriber
        with a callback function, posts an event with a payload, and then removes the subscriber using the -= operator. The test
        asserts that the payload received by the subscriber's callback function is equal to the expected payload.
        """
        event = Event("test_event")

        def on_event(payload):
            """
            A helper function used in the TimerEvent tests to assert that the payload received by the subscriber's callback function
            is equal to the expected payload.
            """
            self.assertEqual(payload, "test_payload")
        event += {"name": "test_subscriber", "on_event": on_event}
        event.post("test_payload")
        event -= "test_subscriber"

    def test_isub(self):
        """
        Test the removal of a subscriber from an event using the -= operator. The test creates an Event object, adds a subscriber
        with a callback function, posts an event with a payload, and then removes the subscriber using a dictionary with the same
        name and callback function. The test asserts that the payload received by the subscriber's callback function is equal to
        the expected payload.
        """
        event = Event("test_event")

        def on_event(payload):
            """
            A helper function used in the TimerEvent tests to assert that the payload received by the subscriber's callback function
            is equal to the expected payload.
            """
            self.assertEqual(payload, "test_payload")
        event += {"name": "test_subscriber", "on_event": on_event}
        event.post("test_payload")
        event -= {"name": "test_subscriber", "on_event": on_event}


if __name__ == '__main__':
    unittest.main()
