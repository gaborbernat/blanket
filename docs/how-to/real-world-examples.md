# Test real-world patterns

These examples test the patterns you meet most often in multithreaded code: ordered access to a lock, a broadcast that
wakes several waiters, and a pool that hands a resource from one thread to another. Each one is a complete, runnable
pytest test. Together they form a small test module you can copy and adapt.

Every example follows the same shape: build the scenario and primitives, register the workers, drive them inside the
`with scenario:` block, then assert on the result. Each one is adapted from blanket's own test suite, so the patterns
match real, passing usage.

## Control who gets a lock first

A lock under contention hands itself to whichever waiter the operating system favors. To test the order your code
depends on, drive it yourself. `assign` gives the lock to a thread; called with two threads, the first releases and the
second acquires.

```python
import blanket

def test_lock_order():
    scenario = blanket.Scenario()
    lock = scenario.Lock()
    lock_api = scenario.api(lock)
    order = []

    def worker(name):
        lock.acquire()
        order.append(name)
        lock.release()

    a = scenario.thread(worker, "A")
    b = scenario.thread(worker, "B")

    with scenario:
        lock_api.assign(b)              # B acquires first
        lock_api.assign(b, a)           # B releases, A acquires
        lock_api.unblock(lock.release, a)  # let A release

    assert order == ["B", "A"]
```

## Wake broadcast waiters in a chosen order

An `Event` releases every waiter at once when it is set, and the wake order is out of your hands. `cycle` puts you in
charge: it drives the waiters to their `wait` calls and the setter to its `set`, then lets you `wake` them one at a
time.

```python
import blanket

def test_event_broadcast():
    scenario = blanket.Scenario()
    event = scenario.Event()
    event_api = scenario.api(event)
    log = []

    def waiter(name):
        def run():
            event.wait()
            log.append(name)
        return run

    def setter():
        event.set()
        log.append("set")

    with scenario:
        a = scenario.thread(waiter("A"))
        b = scenario.thread(waiter("B"))
        x = scenario.thread(setter)
        with event_api.cycle(a, b, x) as cycle:
            cycle.wake(b)               # wake B before A

    assert log == ["B", "A", "set"]
```

## Hand a resource between threads

A `Semaphore` models a pool of interchangeable resources, such as database connections. Start it empty, then test that a
waiter blocks until another thread returns a resource. `allocate` drives an ordered sequence of releases and acquires,
sorting out which thread does which from the method it calls.

```python
import blanket

def test_pool_handoff():
    scenario = blanket.Scenario()
    pool = scenario.Semaphore(0)        # no free slots
    pool_api = scenario.api(pool)
    log = []

    def borrower():
        log.append("waiting")
        pool.acquire()                  # block until a slot frees
        log.append("acquired")

    def returner():
        pool.release()                  # return a slot
        log.append("returned")

    with scenario:
        r = scenario.thread(returner)
        b = scenario.thread(borrower)
        list(pool_api.allocate(r, b))   # returner frees a slot, then borrower takes it

    assert log == ["waiting", "returned", "acquired"]
```

## A complete test module

The three tests above already form a runnable module. Save them in `test_scheduling.py` and run them with pytest:

```console
$ pytest test_scheduling.py
```

Each test produces the same result on every machine and every run, so none of them needs a rerun marker.
