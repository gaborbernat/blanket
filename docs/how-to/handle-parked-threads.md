# Handle parked threads at exit

When the scheduler leaves the `with scenario:` block, blanket cleans up parked workers for you. This guide covers what
that cleanup does, when it is enough, and when you need to drive a thread yourself.

## What exit does

On exit, blanket runs these steps in order:

1. Close any still-active `Driver`.
1. Flip the scenario to unregulated. From here, calls on the blanket primitives behave like calls on the real primitives
   and no longer park.
1. Unpark every transaction sitting at a blanket-controlled park (`BLOCKED`, `STALLED`, or `PAUSED`), so its worker
   resumes and finishes the call against the now-unregulated primitive.
1. Join every managed worker thread.

In the common case you do not drive parked workers to completion before exit. The exit unparks them and they finish on
their own.

## When exit can still hang

A thread parked at `WAITING` is asleep inside a real `condition.wait`, `lock.acquire`, or `barrier.wait`. blanket does
not unpark it, because that wait belongs to the underlying primitive, not to blanket. The OS-level wait returns only
when its natural wake condition fires (a notify, an event set, the last barrier party arriving) or its timeout expires.
If your test never provides that wake, the join hangs.

> [!WARNING]
> A worker left at `WAITING` with no path to wake will hang the scenario exit. Provide the wake, give the call a
> timeout, or drive the thread to a terminal state before you exit.

## Drive a thread to termination yourself

When you want explicit control over how a thread ends, drive specific final calls or expire its timeout, call
`scenario.finish(*threads)` inside the scenario before exit.

```python
with scenario:
    ...
    scenario.finish(A, B)
```

The auto-unpark at exit covers the "let the worker finish on its own" case. `finish` covers the cases where you want to
choose the ending.

## Setup, teardown, and raw handles

For setting up or tearing down synchronization state, you rarely need raw handles. Outside the `with scenario:` block,
blanket primitives are unregulated, so calls on the regulated handle pass straight through.

```python
event = scenario.Event()
event.set()        # outside the scenario; passes through

lock = scenario.Lock()
lock.acquire()     # also passes through
```

Raw handles cover the two cases where regulation would otherwise apply but you do not want it: the scheduler making an
unregulated call from inside the scenario, such as `scenario.raw(sem).release()`, or handing an unregulated handle to a
worker you do not want to script. Regulation tracks the handle, not the primitive, so a regulated handle and a raw
handle to the same primitive coexist in one test.
