# Wait on signals

`scenario.wait(*items, timeout=None)` blocks the scheduler until one of the items you pass it signals. A signal is an
observable condition becoming true: a thread terminating, a transaction reaching a state, a method being called. The
design follows Win32's
[`WaitForMultipleObjects`](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitformultipleobjects).

## Wait for any of several conditions

Pass as many items as you want. `wait` returns as soon as any one of them signals, and returns a `set` of the items that
signaled.

```python
from blanket import Terminated, Reached, State

signaled = scenario.wait(Terminated(A), Reached(b_tx, State.WAITING))
if Terminated(A) in signaled:
    ...
```

To wait for every item rather than any item, call `wait` once per item.

## What you can wait on

| Item                                         | Signals while                                       |
| -------------------------------------------- | --------------------------------------------------- |
| a thread                                     | the thread has an active transaction                |
| a transaction                                | once the transaction has completed                  |
| a bound method, `lock.acquire`               | any thread has an active transaction on that method |
| `Call(thread, method)`                       | `thread` is calling `method`                        |
| `Use(thread, primitive)`                     | `thread` is calling any method on `primitive`       |
| `Terminated(thread)`                         | once `thread` has terminated                        |
| `Not(token)`                                 | the wrapped token is not signaling                  |
| `Nested(transaction)`                        | the transaction has a child transaction in flight   |
| `Action(transaction)`                        | the transaction is in its action phase              |
| `Reached(transaction, state)`                | the transaction's state is at or past `state`       |
| a `TransactionState` subclass, `Waiting(tx)` | the transaction is exactly in that state            |
| the scenario itself                          | you have entered the scenario                       |

The `TransactionState` subclasses are `Blocked`, `Commit`, `Waiting`, `Stalled`, `Resumed`, `Committed`, `Paused`,
`Exiting`, `Returned`, and `Raised`. Each signals only while `tx.state` is the matching state.

## Add a timeout

`timeout` is the longest the call waits, in seconds. It defaults to `None`, which waits forever. A `wait` that times out
raises [`TimeoutError`](https://docs.python.org/3/library/exceptions.html#TimeoutError).

```python
scenario.wait(t, timeout=5.0)
```

> [!TIP]
> `Reached(tx, state)` signals at or past a state, so it stays signaled once the transaction moves on. A
> `TransactionState` token signals only during that exact state. Reach for `Reached` when you want "has it gotten this
> far", and the exact token when you want "is it here right now".

For the full list of states, see [transaction states](../reference/transaction-states.md).
