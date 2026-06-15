# Glossary

```{glossary}
scenario
  The top-level object that owns a set of blanket primitives and any managed
  worker threads. Create one with `blanket.Scenario()`.

enter the scenario
  To enter the `with scenario:` block. Most of the interesting APIs require it.
  Inside the block, the calling thread is the scheduler.

scheduler
  The thread that drives the worker threads, almost always the test's main
  thread. The role lasts only while that thread is inside the `with scenario:`
  block.

worker thread
  A thread registered with the scenario, usually through `scenario.thread`. Worker
  threads exercise the code under test and use blanket primitives the ordinary
  way. They do not know they are being scripted.

primitive
  A blanket `Lock`, `RLock`, `Condition`, `Semaphore`, `BoundedSemaphore`,
  `Event`, or `Barrier`, built on the scenario. Also called a primitive handle.

raw
  A second handle to the same underlying primitive whose calls skip regulation and
  run at once. Reach it with `scenario.raw(primitive)` or
  `scenario.raws[primitive]`. Useful only inside the scenario.

actual
  A real [`threading`](https://docs.python.org/3/library/threading.html) primitive. blanket wraps one inside each of its primitives.
  You do not handle actuals directly.

transaction
  The wrapper blanket builds around each method call on a primitive. It holds a
  state, a method, a thread, and the operations the scheduler can run on it. The
  unit blanket works in.

tempo
  The linearized sequence of synchronization calls the scheduler is letting
  complete. The core move in blanket is to decide the tempo, then make it so.

signal
  An observable condition the scheduler can wait on: a thread terminating, a
  transaction reaching a state, a method being called.

parking
  Making a thread stop and wait. A parked transaction sits in one of its parking
  states until the scheduler (or, for `WAITING`, the underlying primitive) releases
  it.

scheduler block
  The parking state before the real method runs (`BLOCKED`).

scheduler stall
  A mid-transaction park used by certain transactions (`STALLED`).

scheduler pause
  A general-purpose park usable at any point (`PAUSED`).

actual wait
  The parking state inside the real method call (`WAITING`). blanket cannot
  control it; the underlying primitive does.
```
