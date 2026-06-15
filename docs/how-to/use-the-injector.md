# Inject a synchronization point

The scenario model assumes the code under test uses synchronization primitives. blanket wraps those primitives and the
scheduler steers from there. Some code uses none: lockless data structures, or code that leans on a Python operation
being atomic at the bytecode level, such as `dict[k] = v` or `list.append`. There is nothing for blanket to wrap, so the
threads race ahead and the test goes back to being nondeterministic.

The bytecode injector, in `blanket.injector`, solves this. It copies a function and inserts one call into the copy's
bytecode at a location you choose. Point that call at a synchronization point, such as a real
[`threading.Event`](https://docs.python.org/3/library/threading.html#threading.Event)'s `wait`, and you regain control
over when the function makes progress.

This is a small, optional piece. Skip it unless you have code with no primitives to wrap.

## Find a location

A `Location` marks a point in a function's bytecode. Build one with a classmethod:

- `Location.position(function, line, column=1)` finds a point by source position. `line` is relative to the start of the
  function and 1-based.
- `Location.text(function, text, *, skip=0, after=None)` finds the first occurrence of `text` in the function's source,
  optionally skipping earlier matches or requiring the match to come after another location.
- `Location.token(function, token, *, skip=0, after=None)` finds the first occurrence of a Python token.
- `Location.bytecode(function, offset, stop=None)` takes a raw bytecode offset, for when you built the function with a
  bytecode library and the other methods cannot see its source.

Locations support equality, hashing, and comparison when they come from the same function.

## Inject the call

`inject_call(injected_function, location, *, name='')` builds a new function from the original plus the inserted call.
It does not modify the original.

```python
from blanket.injector import Location, inject_call

def target(x):
    y = x * 2
    return y + 1

def callback():
    print("hello from the injection point")

loc = Location.text(target, "y = x * 2")
new_target = inject_call(callback, loc)
new_target(5)
# prints "hello from the injection point", returns 11
```

blanket binds the injected callable into the new function's globals under its `__name__`, resolving collisions. Override
the name with `name=`.

## Park a thread on demand

The common use: create a real [`threading.Event`](https://docs.python.org/3/library/threading.html#threading.Event),
inject a call to its `wait` into the function, then run the function on another thread. The thread parks at the injected
`wait()` and resumes only when you call `event.set()`.

`inject_call` works on functions and methods. For a method, build a subclass that replaces the method with the injected
version, or overwrite the attribute on the class directly.

Injected code and blanket primitives compose. The two techniques are orthogonal, so you can mix them in one test.
