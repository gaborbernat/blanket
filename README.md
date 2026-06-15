# blanket

## Deterministic multithreaded testing for Python

##### Copyright 2025-2026 by Larry Hastings

> *Your test should be effectively single-threaded*. *If it isn't, you haven't blanketed hard enough*. *Slow it down*.

blanket writes deterministic tests for multithreaded Python code.

Most multithreaded Python test suites carry at least one test marked `@pytest.mark.flaky(reruns=5)`. Threading bugs come
from ordering: two threads touch shared state, and the failure depends on which one runs first. The operating system
picks that order, so the failure is hard to reproduce, and a test that cannot reproduce a bug cannot guard against it.
As Edward Lee put it, threads "discard ... understandability, predictability, and determinism." As free-threaded Python
spreads, more code runs into this.

blanket replaces the synchronization primitives from the `threading` module (`Lock`, `RLock`, `Condition`, `Semaphore`,
`BoundedSemaphore`, `Event`, and `Barrier`) with wrappers that pause on every call and wait for instructions. Inside a
test, your main thread becomes the scheduler and chooses the order. The same interleaving runs on every machine, on
every run.

blanket wraps the real primitives rather than reimplementing them. A `scenario.Lock()` calls a real `threading.Lock`
underneath, so it behaves the way production behaves. Your test controls when each call runs, not how it behaves. To
make this work, the code under test uses scenario primitives in place of the real ones.

## Requirements

blanket runs on Python 3.11 or newer. It depends on [big](https://github.com/larryhastings/big), and the optional
bytecode injector needs [bytecode](https://pypi.org/project/bytecode/). blanket is pure Python.

```console
$ pip install blanket
```

## Quick start

Three threads share one lock and a barrier. With the real `threading` primitives, the operating system decides the
order, and it changes from run to run:

```python
import random
import threading

lock = threading.Lock()
barrier = threading.Barrier(3)

def worker(name):
    with lock:
        print(f"worker {name} got the lock")
    barrier.wait()
    print(f"worker {name} is past the barrier")

threads = [threading.Thread(target=worker, args=(name,)) for name in "ABC"]
random.shuffle(threads)
for t in threads:
    t.start()
for t in threads:
    t.join()
```

The worker is ordinary production code. With blanket, only the setup changes: the primitives come from a scenario, and
the main thread steps the workers through their calls inside the `with scenario:` block.

```python
import blanket

scenario = blanket.Scenario()

lock = scenario.Lock()
barrier = scenario.Barrier(3)

def worker(name):
    with lock:
        print(f"worker {name} got the lock")
    barrier.wait()
    print(f"worker {name} is past the barrier")

A = scenario.thread(worker, "A")
B = scenario.thread(worker, "B")
C = scenario.thread(worker, "C")

lock_api = scenario.api(lock)
barrier_api = scenario.api(barrier)

with scenario:
    list(lock_api.relay(B, A, C))
    lock_api.unblock(lock.release, C)
    with barrier_api.cycle(C, A, B):
        pass
```

The output is the same every run:

```text
worker B got the lock
worker A got the lock
worker C got the lock
worker C is past the barrier
worker A is past the barrier
worker B is past the barrier
```

`relay` passed the lock through B, then A, then C. `unblock` let C run its final `lock.release`. `cycle` walked the
three threads through the barrier and chose the order they resumed in.

## Documentation

The full documentation lives in [`docs/`](docs/index.md) and builds to a site on Read the Docs. It follows the
[Diátaxis](https://diataxis.fr/) structure:

- [Tutorials](docs/tutorials/index.md) teach the basics through a worked example.
- [How-to guides](docs/how-to/index.md) solve specific tasks.
- [Reference](docs/reference/index.md) documents the API, the transaction state machine, and the vocabulary.
- [Explanation](docs/explanation/index.md) covers how blanket works and why.

## License

blanket is released under the MIT license. See [LICENSE](LICENSE).
