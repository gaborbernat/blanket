# Monkey-patch a module

Some code does its threading work through `import threading` and references like
[`threading.Lock`](https://docs.python.org/3/library/threading.html#threading.Lock), or through
`from threading import Lock`. When you do not own that source and cannot pass in pre-built primitives, `scenario.inject`
rewrites those references for you.

## Patch a module for the duration of a block

`scenario.inject(module)` rebinds the threading-primitive references in `module` so that, while the patch is in place,
calls that build a `Lock`, `Condition`, and the rest build blanket primitives on the scenario instead. The return value
is a handle that works as a context manager.

```python
import target_module
import blanket

scenario = blanket.Scenario()
with scenario.inject(target_module):
    # Inside this block, target_module.threading.Lock(),
    # target_module.threading.Condition(), and so on build
    # blanket primitives bound to scenario.
    ...
```

On exit, the original references come back.

## What gets patched

`inject` handles two reference patterns:

- Names bound directly to a threading primitive class, such as `from threading import Lock` or `Mutex = threading.Lock`.
  Each such name is rebound to the matching scenario primitive class. The match is by value, not by name, so an
  unrelated object that happens to be called `Lock` stays untouched.
- A module attribute whose value is the [`threading`](https://docs.python.org/3/library/threading.html) module itself,
  such as `import threading`. blanket replaces it with a stand-in whose `.Lock`, `.RLock`, and the rest are the
  scenario's primitives, and whose other lookups fall through to the real module. So `target_module.threading.Lock()`
  builds a blanket `Lock`, while `target_module.threading.Thread` stays the real
  [`threading.Thread`](https://docs.python.org/3/library/threading.html#threading.Thread).

## When inject cannot find anything

If `inject` finds no patchable references, it raises
[`ValueError`](https://docs.python.org/3/library/exceptions.html#ValueError). That usually means you pointed it at the
wrong module, or the target imports [`threading`](https://docs.python.org/3/library/threading.html) lazily inside a
function, so the import has not run yet when `inject` looks.

> [!CAUTION]
> You can patch a module more than once. If you do, undo the patches in reverse order. After `scenarioA.inject(X)` then
> `scenarioB.inject(X)`, close B before you close A.

See [`scenario.inject`](../reference/api/index.md) in the API reference for the handle's full surface.
