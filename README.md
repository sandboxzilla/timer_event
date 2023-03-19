# Timer Event Package

This package provides two classes for working with events:

*1. EventThread:* A class for creating and managing events with callback routines.\
    This class can be used independently of TimerEvent for handling general event-driven scenarios without any time-based requirements.

*2.  TimerEvent:* A class that extends EventThread to create timer-based 
    events.\
    This class is specifically designed for scenarios where events are triggered after a certain period of time or at specific intervals.\
    **Note:**   Since this class extends the EventThread class it uses most all methods defined and documented in EvenThread class.

## **EventThread:**

The EventThread class creates an event that can be subscribed to and triggered with a payload. The class uses its own thread to broadcast events to subscribers.  The callback function is called when the event is triggered with a payload.

The packet dictionary is passed to the callback.
The packet dictionary includes:
> All parameters passed in during instantiation of the EventThread.
> Minimum items included: ..
    "event" =   The event name
    "dest"  =   The subscriber name provided when subscribing\
    "payload" = The object included in the post\
    "cookie" =  The cookie if included when subscribing, otherwise None


The EventThread class has the following methods::

 *subscribe(name: str, on_event: callable):* Subscribes to the event with a callback function.\
 *unsubscribe(name: str):* Unsubscribes from the event.\
 *post(payload, \*\*kwargs):* Posts an event with a payload to the subscribers.\
 *stop():* Stops the event.
 
 ## **TimerEvent:**

The TimerEvent class creates a timed event that triggers at a specified interval. The class uses a Timer object to initiate the timed event. The TimerEvent class can be subscribed to using the subscribe method, which takes a name and a callback function as arguments. The callback function is executed when the timed event is triggered.

The  TimerEvent class has the following methods::

 *subscribe(name: str, on_event: callable):* Subscribes to the timed event with a callback function.\
 *unsubscribe(name: str):* Unsubscribes from the timed event.\
 *start():* Starts the timed event.\
 *stop():* Stops the timed event.\

 ## Example Usage::
<code>

    from timer_event import TimerEvent, EventThread
    import time

     # Create a TimerEvent that triggers every 5 seconds
    te = TimerEvent(interval=5.0)

    # Subscribe to the TimerEvent
    def te_on_event(packet):
        print("TimerEvent triggered")

    te.subscribe(name="test_subscriber", on_event=te_on_event)

    # Start the TimerEvent
    te.start()

    # Create an Event
    event = EventThread("test_event")

    # Subscribe to the Event
    def ev_on_event(payload):
        print(f"Event triggered with payload: {payload}")

    event.subscribe(name="test_subscriber", on_event=ev_on_event)

    # Post an event with a payload
    event.post("test_payload")

    # Sleep to allow for timer events
    time.sleep(10)

    # Stop the TimerEvent and Event
    te.stop()
    event.stop()
    
</code>
