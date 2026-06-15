# Reproduce a flaky test

A flaky test fails for some thread interleavings and passes for others, and CI hits the bad one at random. This guide
turns that intermittent failure into a deterministic test you can keep.

## Start from the symptom

Say a test exercises two workers that both take a lock and record the order they ran. Sometimes CI sees `["A", "B"]` and
sometimes `["B", "A"]`, and an assertion that expects one order fails about half the time. The order is the variable, so
make it an input.

## Pin each ordering

Drive the lock yourself with `assign`. With one thread it acquires; with two, the first releases and the second
acquires. Write one test per ordering you care about.

```python
import blanket

def run(first, second):
    scenario = blanket.Scenario()
    lock = scenario.Lock()
    lock_api = scenario.api(lock)
    order = []

    def worker(name):
        lock.acquire()
        order.append(name)
        lock.release()

    threads = {name: scenario.thread(worker, name) for name in ("A", "B")}

    with scenario:
        lock_api.assign(threads[first])                  # first acquires
        lock_api.assign(threads[first], threads[second]) # first releases, second acquires
        lock_api.unblock(lock.release, threads[second])  # let second release
    return order

def test_a_then_b():
    assert run("A", "B") == ["A", "B"]

def test_b_then_a():
    assert run("B", "A") == ["B", "A"]
```

Both tests pass on every run, on every machine. The interleaving that used to appear at random is now two named cases
your suite covers on purpose.

## Inspect the order blanket chose

When you are not sure which interleaving a test produced, read `scenario.log` inside the scenario. It holds the
completed transactions in the order they finished, so you can recover the exact sequence of synchronization calls. See
[watch the scheduler work](../tutorials/getting-started.md#watch-the-scheduler-work).

## Drop the rerun marker

Once both orderings have deterministic tests, remove the `@pytest.mark.flaky` marker. The failure no longer hides behind
reruns: it either reproduces or it does not.
