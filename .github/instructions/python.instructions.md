---
applyTo: "**/*.py"
---

# Python in this repository

- Pure functions, with input and output at the edges. A function that both decides and writes is two functions.
- Types on every signature. `mypy` runs with `disallow_untyped_defs`, so an untyped function fails the build.
- Google-style docstrings on every module, class and public function. Say what it does and why, not how it got here.
- Pydantic models at every boundary: config files, tool arguments, hook payloads, model answers. Inside, use frozen
  dataclasses. A class holds data, a function does the work.
- Read config with `config_for(__name__, Shape)`. A module's config file mirrors its path under `config/`.
- Order a file bottom-up: helpers above the function that uses them, so it reads from the detail to the result.
- Line length 120. `ruff check` and `ruff format` decide the rest, so do not argue with them by hand.
- KISS, DRY, LEAN. Delete rather than keep for later. No comment that restates the line below it.

This file is deliberately short and self-contained. Instructions are sent with every matching request, and GitHub's
guidance is that pointing them at an external document tends to work badly, so the rules live here rather than in a
link to a longer guide.
