# How-to guides

Each guide solves one task. They assume you already know the basics from the [tutorials](../tutorials/index.md).

- [Test real-world patterns](real-world-examples.md) tests ordered lock access, broadcast wakeups, and resource pools,
  with a complete pytest module.
- [Reproduce a flaky test](reproduce-a-flaky-test.md) turns an intermittent CI failure into a deterministic test you can
  keep.
- [Wait on signals](signals-and-wait.md) blocks the scheduler until a thread, transaction, or method call reaches a
  state you care about.
- [Monkey-patch a module](monkey-patching.md) redirects a third-party module's
  [`threading`](https://docs.python.org/3/library/threading.html) references to blanket primitives.
- [Inject a synchronization point](use-the-injector.md) adds a control point to code that uses no synchronization
  primitives at all.
- [Control how a primitive reports itself](masquerade.md) names a primitive for debugging or keeps it disguised as the
  real thing.
- [Handle parked threads at exit](handle-parked-threads.md) explains the cleanup the scenario runs on exit and when you
  need to drive a thread yourself.
- [Avoid common pitfalls](common-pitfalls.md) lists the mistakes that trip people up and the fix for each.

```{toctree}
---
hidden:
---
real-world-examples
reproduce-a-flaky-test
signals-and-wait
monkey-patching
use-the-injector
masquerade
handle-parked-threads
common-pitfalls
```
