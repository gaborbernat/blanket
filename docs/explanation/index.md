# Explanation

Background on how blanket works and why it is built the way it is. None of this is required to use blanket, but it helps
when you want to understand the API rather than memorize it.

- [Why deterministic threading](why.md) explains when blanket helps, when plain tools are enough, and the honest limits.
- [How it works](how-it-works.md) traces a method call through the scheduler block, the underlying primitive, and back.
- [The scenario](the-scenario.md) explains the scenario object, regulation, and worker threads.
- [The three API layers](the-three-api-layers.md) describes the low, middle, and high level interfaces and when to use
  each.
- [Tools compared](comparisons.md) contrasts blanket with stateless model checkers and related work.

```{toctree}
---
hidden:
---
why
how-it-works
the-scenario
the-three-api-layers
comparisons
```
