# Getting started

This tutorial installs blanket and walks through a first deterministic test. By the end you will have driven three
threads through a lock and a barrier in an order you chose.

> [!IMPORTANT]
> blanket can only steer the primitives it builds. The code under test has to use a scenario's primitives, or have them
> injected, or the scheduler never sees those calls.

## Requirements

blanket runs on Python 3.11 or newer. It depends on [big](https://github.com/larryhastings/big), and the optional
bytecode injector needs [bytecode](https://pypi.org/project/bytecode/). blanket is pure Python.

```console
$ pip install blanket
```

## The problem

Threading bugs come from ordering. Two threads touch shared state, and the failure depends on which one runs first. The
operating system scheduler picks that order, so you cannot reproduce the failure on demand. A test that cannot reproduce
a bug cannot guard against it.

Here is a program with three threads, one lock, and a barrier. Six orders for the lock times six orders for the barrier
give thirty-six possible interleavings, and you get whichever one the scheduler hands you.

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

Run it a few times. The output order changes from run to run.

## The same program under blanket

Now drive the same workers with blanket. The worker function does not change. Only the setup changes: the primitives
come from a scenario, and the main thread steps the workers through their calls inside a `with scenario:` block.

```python
import blanket
import threading

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

The output is the same on every machine, on every run:

```text
worker B got the lock
worker A got the lock
worker C got the lock
worker C is past the barrier
worker A is past the barrier
worker B is past the barrier
```

Three calls did the work. `relay` passed the lock through B, then A, then C. `unblock` let C run its final
`lock.release`. `cycle` walked the three threads through the barrier and chose the order they resumed in.

## Watch the scheduler work

You can see the schedule the test thread chose. Every method call on a regulated primitive becomes a transaction, and
`scenario.log` holds the completed ones in the order they finished. Read it inside the scenario, after the workers have
run, to recover the exact sequence of synchronization calls.

```python
import blanket
from blanket import Terminated

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
names = {a: "A", b: "B"}

with scenario:
    lock_api.assign(b)              # B acquires
    lock_api.assign(b, a)           # B releases, A acquires
    lock_api.unblock(lock.release, a)
    scenario.wait(Terminated(a))
    scenario.wait(Terminated(b))
    schedule = [(names[tx.thread], tx.method.__name__) for tx in scenario.log]

print(schedule)
# [('B', 'acquire'), ('B', 'release'), ('A', 'acquire'), ('A', 'release')]
```

`scenario.log` clears when you leave the scenario, so read it before the block ends.

## The shape every test shares

Every blanket test follows the same three steps.

```python
# 1. Build the scenario, the primitives, and the worker threads.
scenario = blanket.Scenario()
lock = scenario.Lock()

def worker():
    with lock:
        ...

t = scenario.thread(worker)

# 2. Enter the scenario. The main thread is now the scheduler.
with scenario:
    ...

# 3. Exit the scenario, then assert on the result.
assert ...
```

Setup happens before the `with scenario:` block on purpose. Your main thread only holds the scheduler role inside that
block, so anything that does not need scheduler control (creating primitives, defining workers, registering threads)
belongs before it.

The worker code is the production code under test. Workers call `with lock:` and `lock.acquire()` the way they would in
production. blanket asks you to swap the real synchronization objects for scenario primitives, and nothing more.

> [!NOTE]
> A useful test needs two or more worker threads. With a single worker there is no cross-thread ordering to control, and
> nothing for the scheduler to do.

## A note on naming

The examples here follow a small convention, the same one the author uses:

- Threads get single uppercase letters: `A`, `B`, `C`.
- A `Lock` is `lock` and its API object is `lock_api`. The same pattern gives `cond`/`cond_api`, `event`/`event_api`,
  and so on.
- The scenario is `scenario`, or `s` when space is tight.
- Transactions are often abbreviated `tx`.

You are free to name things however you like. This is the convention the documentation uses.

## Where to go next

- Read [the scenario](../explanation/the-scenario.md) to understand regulation, worker threads, and what entering the
  scenario changes.
- Skim [the three API layers](../explanation/the-three-api-layers.md) to see where `relay` and `cycle` sit and what is
  underneath them.
- Browse the [how-to guides](../how-to/index.md) for specific tasks.
