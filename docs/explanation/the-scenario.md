# The scenario

The `Scenario` is the top-level blanket object. It takes no arguments:

```python
scenario = blanket.Scenario()
```

A scenario owns the replacement primitives, manages worker threads, and gives the scheduler its helper methods. Through
one you can build primitives (`scenario.Lock()`), create and manage worker threads (`scenario.thread()`), inspect a
thread's current transaction (`scenario.transaction`), wait for something to happen (`scenario.wait`), drive workers
through method calls (`scenario.park`, `scenario.skip`, `scenario.finish`, and the `Driver`/`Chain`/`Dispatch`
subsystem), and monkey-patch another module to use blanket primitives (`scenario.inject`).

## Regulation: inside versus outside

A primitive is regulated only while you are inside the `with scenario:` block. Outside it, blanket primitives behave
like the real thing: calls pass straight through to the underlying primitive. This is why setup and teardown need no
special handling.

```python
event = scenario.Event()
event.set()          # outside the scenario; passes through

with scenario:
    # inside the scenario, every primitive call parks
    ...

event.clear()        # outside again; passes through
```

Entering the scenario sets the bit that turns parking on. From that point, every method call on a regulated primitive
stops at the scheduler block and waits for you. Exiting clears the bit and unparks any transaction still held at a
blanket-controlled park. You can enter and exit a scenario more than once.

> [!NOTE]
> Outside the scenario you never need raw handles. A regulated handle is already unregulated there. Raw handles matter
> only inside the block.

## Worker threads

Write tests with two or more worker threads doing the work while your main thread enters the scenario and schedules
them. One worker has no one to synchronize with, so there is nothing to control.

Workers exercise the code under test and synchronize through blanket primitives. Done right, they never know they are
running inside blanket. You can build them with
[`threading.Thread`](https://docs.python.org/3/library/threading.html#threading.Thread), but
`scenario.thread(target, *args, **kwargs)` is easier and gives you a managed thread:

- A managed thread created before you enter the scenario starts automatically when you enter.
- A managed thread created inside the scenario starts at once.
- On scenario exit, blanket joins every managed thread.

While a worker runs ordinary Python it runs at full speed. The moment it calls a method on a regulated primitive, the
call parks and sleeps until the scheduler releases it.

## Handles to a primitive

Constructing `scenario.Lock()` returns a primitive handle. Alongside it the scenario keeps an API object, reached with
`scenario.api(lock)`, and a raw handle, reached with `scenario.raw(lock)` or `scenario.raws[lock]`. All point at the
same underlying object, so a method on any of them changes the same state.

The raw handle is always unregulated. It serves two cases inside the scenario. First, the scheduler sometimes needs to
change a primitive's state itself, for example bumping a semaphore with `scenario.raw(sem).release()`. Calling the
regulated handle there would deadlock, because the scheduler would be waiting on its own call to make progress. Second,
you can hand a raw handle to a worker or subsystem you do not want to script. Regulation follows the handle, not the
primitive, so a regulated handle and a raw handle to the same object coexist in one test.

For the masquerade behavior of the primitive handle, see
[control how a primitive reports itself](../how-to/masquerade.md).
