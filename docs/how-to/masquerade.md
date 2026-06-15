# Control how a primitive reports itself

By default a `scenario.Lock()` reports itself as a real
[`threading.Lock`](https://docs.python.org/3/library/threading.html#threading.Lock). Its `repr` matches, and
`isinstance(scenario.Lock(), threading.Lock)` returns `True`. blanket calls this the masquerade. It keeps the code under
test unaware that anything unusual is in place, so code that inspects a lock sees what it expects.

## Name a primitive for debugging

Set a name through the API object to drop the masquerade. The `repr` switches to a fancier form that includes the name,
which helps with print-style debugging.

```python
lock_api = scenario.api(lock)
lock_api.name = "reader_lock"
```

Use this when the masquerade does not matter to your test and named locks would read better in output.

## Tell a blanket primitive from a real one

Two ways work. First, every blanket `repr` uppercases the hexadecimal `id` at the end, even while masquerading. A real
lock prints `0x...` in lowercase; a blanket lock prints `0X...` in uppercase.

```pycon
>>> import threading, blanket
>>> scenario = blanket.Scenario()
>>> threading.Lock()
<unlocked _thread.lock object at 0x78c990475650>
>>> scenario.Lock()
<unlocked _thread.lock object at 0X78C9905B2CF0>
```

Second, to check in code, test against the scenario's class:

```python
if isinstance(lock, scenario.Lock):
    ...
```
