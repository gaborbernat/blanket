# The seven primitives

The [`threading`](https://docs.python.org/3/library/threading.html) module has seven synchronization primitives. A
scenario provides the same seven, with the same names and the same method signatures. Each is built as a method on the
scenario, for example `scenario.Lock()`. Outside the scenario they behave like the real primitives; inside it they are
regulated.

| Primitive        | Constructor                                            |
| ---------------- | ------------------------------------------------------ |
| Lock             | `scenario.Lock()`                                      |
| RLock            | `scenario.RLock()`                                     |
| Condition        | `scenario.Condition(lock=None)`                        |
| Semaphore        | `scenario.Semaphore(value=1)`                          |
| BoundedSemaphore | `scenario.BoundedSemaphore(value=1)`                   |
| Event            | `scenario.Event()`                                     |
| Barrier          | `scenario.Barrier(parties, action=None, timeout=None)` |

## Methods

- **`scenario.Lock()`**: `acquire(blocking=True, timeout=-1)`, `release()`, `locked()`, `__enter__`/`__exit__`.
- **`scenario.RLock()`**: `acquire(blocking=True, timeout=-1)`, `release()`, `locked()` where supported,
  `__enter__`/`__exit__`. Reentrancy comes from the real
  [`threading.RLock`](https://docs.python.org/3/library/threading.html#threading.RLock).
- **`scenario.Condition(lock=None)`**: `acquire(...)`, `release()`, `wait(timeout=None)`,
  `wait_for(predicate, timeout=None)`, `notify(n=1)`, `notify_all()`, `__enter__`/`__exit__`.
- **`scenario.Semaphore(value=1)`**: `acquire(blocking=True, timeout=None)`, `release(n=1)`, `__enter__`/`__exit__`.
- **`scenario.BoundedSemaphore(value=1)`**: same as `Semaphore`. `release` raises if it would exceed the initial value.
- **`scenario.Event()`**: `is_set()`, `set()`, `clear()`, `wait(timeout=None)`.
- **`scenario.Barrier(parties, action=None, timeout=None)`**: `wait(timeout=None)`, `reset()`, `abort()`, plus the
  `parties`, `n_waiting`, and `broken` properties.

Every primitive also has a settable `name` property. Setting it drops the masquerade; see
[control how a primitive reports itself](../how-to/masquerade.md).

For what each method does in the state machine, see [transaction states](transaction-states.md).
