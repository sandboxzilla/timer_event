# Timer Event Package

The Timer Event package provides classes for creating timed threaded events and subscribing to them. The package includes the following classes:
*TimerEvent:* A class for creating timed events that trigger at a specified interval.
*Event:* A class for creating events that can be subscribed to and triggered with a payload.

## **TimerEvent:**

The TimerEvent class creates a timed event that triggers at a specified interval. The class uses a Timer object to initiate the timed event. The TimerEvent class can be subscribed to using the subscribe method, which takes a name and a callback function as arguments. The callback function is executed when the timed event is triggered.

The  TimerEvent class has the following methods::

 subscribe(name: str, on_event: callable): Subscribes to the timed event with a callback function.
 unsubscribe(name: str): Unsubscribes from the timed event.
 start(): Starts the timed event.
 stop(): Stops the timed event.

## **Event:**

The Event class creates an event that can be subscribed to and triggered with a payload. The class uses a thread to post events to subscribers. The Event class can be subscribed to using the subscribe method, which takes a name and a callback function as arguments. The callback function is executed when the event is triggered with a payload.

The Event class has the following methods::

 subscribe(name: str, on_event: callable): Subscribes to the event with a callback function.
 unsubscribe(name: str): Unsubscribes from the event.
 post(payload, \*\*kwargs): Posts an event with a payload to the subscribers.
 stop(): Stops the event.
 
 ## Example Usage::

    from timer_event import TimerEvent, Event
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
    event = Event("test_event")

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
