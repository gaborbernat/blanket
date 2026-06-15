# blanket

blanket writes deterministic tests for multithreaded Python code.

It replaces the synchronization primitives from the [`threading`](https://docs.python.org/3/library/threading.html)
module (`Lock`, `RLock`, `Condition`, `Semaphore`, `BoundedSemaphore`, `Event`, and `Barrier`) with wrappers that pause
on every call and wait for instructions. Inside a test, your main thread becomes the scheduler: it decides which thread
acquires the lock next, which waiter a `notify()` wakes, and what order threads leave a barrier. The same interleaving
runs on every machine, on every run.

blanket wraps the real primitives rather than reimplementing them. A `scenario.Lock()` calls a real
[`threading.Lock`](https://docs.python.org/3/library/threading.html#threading.Lock) underneath, so it behaves the way
production behaves. Your test controls when each call runs, not how it behaves.

> [!IMPORTANT]
> blanket can only steer the primitives it builds. The code under test has to use a scenario's primitives, or have them
> injected, or the scheduler never sees those calls.

## Find your way around

This documentation follows the [Diátaxis](https://diataxis.fr/) structure. Pick the entry point that matches what you
need right now.

- [Tutorials](tutorials/index.md) teach the basics through a worked example. Read these first if blanket is new to you.
- [How-to guides](how-to/index.md) solve specific tasks: monkey-patching a module, waiting on signals, injecting
  synchronization points into code that has none.
- [Reference](reference/index.md) describes the API surface, the transaction state machine, and the vocabulary.
- [Explanation](explanation/index.md) covers how blanket works under the hood and why the API is shaped the way it is.

## Project links

- [Source code](https://github.com/larryhastings/blanket) on GitHub
- [Package](https://pypi.org/project/blanket/) on PyPI
- [big](https://github.com/larryhastings/big), the support library blanket builds on
- [bytecode](https://bytecode.readthedocs.io/), used by the optional injector

```{toctree}
---
hidden:
maxdepth: 2
---
tutorials/index
how-to/index
reference/index
explanation/index
```
