# FAQ

## Do I have to change my production code?

You swap the synchronization primitives, not the logic. The code under test calls `acquire`, `release`, `wait`, and the
rest exactly as before; it just gets them from a scenario instead of the `threading` module. When you cannot pass
primitives in, [`scenario.inject`](../how-to/monkey-patching.md) redirects a module's references for you.

## Does blanket reimplement the primitives?

No. Each blanket primitive wraps a real `threading` one and calls it underneath. The semantics come from the standard
library, so your test exercises the real primitive rather than a model of it. See
[how it works](../explanation/how-it-works.md).

## Does it work with free-threaded Python?

Yes. blanket controls ordering through the primitives regardless of whether the GIL is present. Free-threaded builds
surface more ordering bugs, which is part of why deterministic tests matter.

## Which Python versions are supported?

Python 3.11 and newer.

## Is it slow?

blanket runs every regulated operation under a single lock, which keeps its internal model simple and consistent. The
lock is lightly contended in practice. blanket is built for deterministic tests, not for raw throughput, so it is not
tuned to race through millions of interleavings the way a model checker is.

## Can I test code that uses no synchronization primitives?

Yes. The [injector](../how-to/use-the-injector.md) inserts a synchronization point into a function's bytecode, which
gives the scheduler something to control even in lockless code.

## How many worker threads do I need?

Two or more. A single worker has nothing to synchronize against, so there is no ordering for the scheduler to control.

## Does it work with asyncio?

No. blanket targets the `threading` primitives. Coroutine scheduling is a different model.

## Can blanket discover concurrency bugs on its own?

That is not its purpose. blanket reproduces a concurrency scenario you describe, deterministically and by hand. Tools
aimed at discovery work differently; see [tools compared](../explanation/comparisons.md).
