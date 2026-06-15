# API reference

The pages below are generated from the source docstrings by
[Sphinx autodoc](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html) with
[napoleon](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html).

> [!NOTE]
> These pages render on the documentation site. Viewed as raw Markdown on GitHub, they show the autodoc directive source
> rather than the generated reference.

```{eval-rst}
.. automodule:: blanket
   :no-members:
```

The public API splits across two modules:

- [Primitives and scenario](primitives.md) covers `Scenario`, the seven primitives, the signal tokens, and the
  transaction surface.
- [Injector](injector.md) covers `Location` and `inject_call`.

```{toctree}
---
hidden:
---
primitives
injector
```
