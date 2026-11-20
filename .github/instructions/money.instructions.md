---
applyTo: "src/subfinder/lib/statement/**,src/subfinder/config/statement/**,tests/statement/**"
---

# Money in the statement code

- Every amount is `Money` from `transactions.py`, which is a `Decimal` with two decimals. Never `float`: 99.10 as a
  float is not 99.10, and the error turns up in a total rather than where it was made.
- Amounts cross every JSON and YAML boundary as strings, such as `"99.00"`. A JSON number would arrive as a float.
- A negative amount is money out. A charge is negative, and a saving is the positive number you get by negating it.
- The statement is made up, and it stays made up. Do not add a real bank's format, a real merchant or a real person.

This file is loaded only when a file under one of the `applyTo` globs is in play, so it costs nothing in a session
that never touches the statement. That is the whole reason it is a separate file instead of a paragraph in
`copilot-instructions.md`.
