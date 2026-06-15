# Why deterministic threading

Most ways of testing multithreaded code try to provoke a bug by running the code many times and hoping the bad ordering
shows up. blanket takes the opposite approach: you state the ordering, and the test reproduces it on every run. This
page covers when that trade is worth it, and when it is not.

## The trouble with stress-testing concurrency

A race condition fails only for some interleavings of the threads. The operating system chooses the interleaving, so a
test that runs the code once samples one ordering out of many. Teams work around this in a few ways, and each carries a
cost:

- Rerun until green (`@pytest.mark.flaky(reruns=5)`) hides the failure instead of explaining it, and it slows the suite.
- Sleeps between steps (`time.sleep`) encode a guess about timing. They make the test slower and still flake on a loaded
  machine.
- Stress loops that run the body thousands of times raise the odds of hitting the bug but never guarantee it, and a
  failure is still hard to reproduce.

None of these can assert "when B releases the lock while A is waiting, A wins." They can only wait and hope.

## What blanket gives you

blanket makes the ordering an input to the test. You decide which thread acquires the lock next and which waiter a
notify wakes, so the interleaving that triggers the bug runs on demand, the same way on every machine. A failing case
becomes a regression test you can keep, and a rare race becomes reachable for coverage.

It does this without a model of the primitives. Each call runs the real `threading` object underneath, so the behavior
you test is the behavior you ship.

## When plain tools are enough

Reach for ordinary tests, not blanket, when:

- The code is single-threaded, or the threads never touch shared state.
- You are testing throughput or load, where the point is many real interleavings rather than one chosen one.
- A higher-level abstraction already serializes the work (a queue, a single worker, an executor) and you can test that
  abstraction directly.

## What blanket does not do

- It does not search for bugs. blanket reproduces an ordering you describe; it will not discover an interleaving you did
  not think of. Tools built for that are covered in [tools compared](comparisons.md).
- It does not drive the operating system scheduler directly. It controls the synchronization primitives, so code with no
  primitives needs an [injected synchronization point](../how-to/use-the-injector.md).
- It is built for deterministic tests, not for speed. Running millions of interleavings is a job for a model checker.

If a bug depends on a specific ordering and you want a test that pins it down, blanket fits. If you want a tool to go
find orderings you have not imagined, you want something else.
