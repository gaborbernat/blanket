# Avoid common pitfalls

A short list of mistakes that trip people up, with the fix for each.

## The code under test still uses real primitives

blanket can only steer the primitives it created. If the code under test imports `threading` and builds its own `Lock`,
those calls run at full speed and the scheduler never sees them.

Fix: hand the code scenario primitives instead of real ones, or redirect its references with
[`scenario.inject`](monkey-patching.md). For code that uses no primitives at all, add one with the
[injector](use-the-injector.md).

## Only one worker thread

With a single worker there is no cross-thread ordering to control, so there is nothing for the scheduler to do, and the
test proves nothing about concurrency.

Fix: write tests with two or more workers, and keep the main thread as the scheduler.

## Expecting regulation outside the scenario

A common assumption is that blanket primitives always pause. They do not. Outside the `with scenario:` block they are
unregulated: a call passes straight through to the real primitive and returns at once. This is on purpose, and it is why
setup and teardown need no special handling.

```python
event = scenario.Event()
event.set()        # outside the scenario; runs immediately
```

Fix: do the work that needs scheduler control inside the block, and let setup and teardown sit outside it.

## Driving a regulated handle from the scheduler

Inside the scenario, the scheduler must not call a regulated method itself. The call would park waiting for the
scheduler, and the scheduler is the one who would have to release it, so the test deadlocks.

Fix: use a raw handle for scheduler-side changes, for example `scenario.raw(sem).release()`. See
[handle parked threads](handle-parked-threads.md) for more on raws.

## A worker left asleep inside a real primitive

A thread parked at `WAITING` is asleep inside a real `wait` or contended `acquire`. blanket cannot wake it; only a
notify, a release, the last barrier party, or a timeout can. If your test never provides that wake, scenario exit hangs
on the join.

Fix: provide the wake, give the call a timeout, or drive the thread to a terminal state with `scenario.finish` before
exit. See [handle parked threads](handle-parked-threads.md).

## Setup inside the scenario

Creating primitives, defining workers, and registering threads do not need scheduler control. Doing them inside the
block mixes setup with scheduling and makes the test harder to read.

Fix: do all setup before `with scenario:`, then enter the block only to drive the workers.
