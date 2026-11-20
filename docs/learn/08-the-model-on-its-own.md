# 8. The model on its own

## What this path is

Your own program calling a model's API. No Copilot anywhere, which means **nothing from the previous six chapters is
loaded**: no instructions, no skill, no custom agent, and no hook.

It is not one of GitHub's seven types, because there is no Copilot in it. It is in this repository because leaving it
out would hide the most useful comparison: how much of what the other six give you is actually load-bearing, and what
you have to do yourself when none of it is there.

```bash
uv run subfinder run          # prints the plan and stops
uv run subfinder run --yes    # makes the call
```

## One call, not an agent

[clean_merchants.py](../../src/subfinder/lib/api/clean_merchants.py) makes exactly one request. It turns 22 raw
descriptions into a merchant and a category each. [run.py](../../src/subfinder/lib/api/run.py) does everything else
as arithmetic.

Nothing in that job has to decide what to do next. The input and the output are both known in advance. An agent loop
would add cost, latency and ways to fail, for nothing. The documented advice across every vendor is the same: use the
simplest tier that works, and an agent is only worth it when the steps cannot be known up front.

This is the shape most real "AI features" should be, and it is worth noticing that the part of this repository that
does the actual job is the part with no agent in it.

## A schema the API enforces

```python
"response_format": {
    "type": "json_schema",
    "json_schema": {
        "name": CONFIG.schema_name,
        "strict": True,
        "schema": CleanedLines.model_json_schema(),
    },
}
```

The schema comes from the same Pydantic model the rest of the code uses, so there is one definition of the shape.
`strict` makes the API hold the answer to it, rather than asking the model nicely for JSON and hoping.

**The schema fixes the shape, not the content.** A valid answer can still leave a line out, so the code checks:

```python
def _check_every_line_came_back(descriptions, lines) -> None:
    missing = sorted(set(descriptions) - {line.description for line in lines})
    if missing:
        raise ValueError(f"The model did not clean these lines: {missing}")
```

## Three answers that are not answers

A 200 response is not the same as a usable one. The code looks for all three:

| What came back | How to spot it |
|---|---|
| A refusal | `message.refusal` is set. The HTTP status is still 200 |
| Nothing | `message.content` is empty, usually with `finish_reason: "length"` |
| No choice at all | `choices` is empty |

A refusal arriving as an ordinary success is the one that catches people, because the obvious code reads
`content` and gets `None`.

## No sampling parameters

No `temperature`, `top_p` or `seed` is sent, and a test asserts they stay out. GitHub Models serves many models from
several publishers, and one that rejects a parameter it does not support would fail the whole call for no gain. The
defaults are what the catalog's own examples use.

## The checks have to be called by hand

This is the chapter's real point. In [chapter 5](05-hooks.md) the `preToolUse` hook stood between the model and every
write. Here there is no hook, because there is no Copilot to run one. So the code calls the same functions:

```python
def tag_checked(tag: Tag) -> None:
    _require(check_tag(tag, load_workbook().tags, STATEMENT))
    tag_subscription(tag.merchant, tag.transaction_ids)
```

That is why [checks.py](../../src/subfinder/lib/hooks/checks.py) holds pure functions that import nothing about
Copilot. If the checks had been written inside the hook handler, this path would have had to duplicate them, and the
two copies would have drifted.

Two tests make the point directly: `test_the_check_stops_a_bad_tag_with_no_hook_around` and
`test_the_check_stops_an_overclaim_with_no_hook_around`.

## Why GitHub Models, and what is not verified

Any provider would do, since no Copilot is involved. GitHub Models fits the repository, speaks the OpenAI
chat-completions shape, and costs nothing within your account's rate limits, so a reader can try it without a bill.
It needs a fine-grained token with the `models:read` permission, which the token `gh auth login` stores does not
have.

**This path has not been run.** `models.github.ai` was unreachable from the machine this was built on: every path
returned a bare `OK`. So the endpoint, the model id and the request shape come from the documentation, and the tests
check the code against a stand-in transport rather than the live API. The model id is in config and overridable with
`SUBFINDER_MODEL`, because catalogs change; check it against `gh models list` first.

Saying so is cheaper than being caught. A template whose untested path looked tested would be a bad one to copy.

## In the code

- [clean_merchants.py](../../src/subfinder/lib/api/clean_merchants.py): the request, the schema, and reading the answer
- [config/api/clean_merchants.yaml](../../src/subfinder/config/api/clean_merchants.yaml): the endpoint, the limits and
  the system prompt
- [run.py](../../src/subfinder/lib/api/run.py): the whole job, calling the checks itself
- [scripted.py](../../src/subfinder/lib/api/scripted.py): the hand-written correct answer, used wherever no call may
  happen
- [test_clean_merchants.py](../../tests/api/test_clean_merchants.py): a refusal, an empty answer, a missing line, and
  an HTTP error
