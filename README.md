# celery-context-headers

Propagate per-request **context** (trace IDs, tenant, debug flags, locales, etc.) from your **producer** to Celery **workers** — without polluting task signatures.

This package provides a lightweight, generic helper to **inject message headers into any Celery Signature/canvas** (task, chain, group, chord, links) and a simple API to send tasks (`TaskSender`).

## Install

```bash
pip install celery-context-headers
```

Requires: Python 3.9+, Celery 5.3+

## Manage with **uv** (recommended)

- Create a project env + install deps (prod + dev):  
  ```bash
  uv sync
  ```
- Run tests:  
  ```bash
  uv run pytest -q
  ```
- Add dev tools later (example):  
  ```bash
  uv add --dev ruff
  ```
- Build the package:  
  ```bash
  uv build --no-sources
  ```
- Publish to PyPI (uses token or Trusted Publishing):  
  ```bash
  uv publish
  ```

## Quickstart

### 1) Define a headers provider (e.g., using `contextvars`)
```python
# context.py (your app)
from contextvars import ContextVar

trace_id_var = ContextVar("trace_id", default=None)
tenant_id_var = ContextVar("tenant_id", default=None)
debug_var    = ContextVar("debug", default=None)  # JSON-serializable

def current_headers() -> dict:
    h = {}
    if (v := trace_id_var.get()): h["trace_id"] = v
    if (v := tenant_id_var.get()): h["tenant_id"] = v
    if (v := debug_var.get()): h["debug"] = v
    return h
```

### 2) Send tasks with headers
```python
from celery_context_headers import TaskSender
from celery import chain, group
from tasks import add, agg  # your bound tasks reading self.request.headers
from context import current_headers

sender = TaskSender(current_headers)

# like .delay(...) but header-aware
res1 = sender.delay(add, 2, 3)

# send any canvas
res2 = sender.send(chain(add.s(1,2), add.s(3)))

# add extra per-call headers
res3 = sender.send(add.s(10, 20), extra_headers={"debug": {"trace": True}})
```

### 3) Worker-side usage
```python
# tasks.py
from celery import Celery
app = Celery("proj", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0")

@app.task(bind=True)
def add(self, x, y):
    hdrs = self.request.headers or {}
    if hdrs.get("debug", {}).get("trace"):
        print(f"[trace {hdrs.get('trace_id')}] add({x},{y})")
    return x + y
```

## API

```python
from celery_context_headers import TaskSender, apply_headers, deep_set_headers
```

- `TaskSender(headers_provider)`: create a sender bound to your provider.
  - `.delay(task, *args, **kwargs)`: header-aware replacement for `task.delay(...)`.
  - `.send(signature, extra_headers=None, **apply_async_kwargs)`: attach headers (deep) then `apply_async()`.
  - `.with_headers(signature, extra_headers=None, deep=True) -> Signature`: returns a cloned signature with headers set (deep by default).
- `apply_headers(signature, headers) -> Signature`: shallow header set.
- `deep_set_headers(signature, headers) -> Signature`: deep header set across chains, groups, chords, links.

## Examples

See [`examples/`](./examples) for a Redis-based sandbox and a FastAPI middleware snippet that populates contextvars per request.

## Development

```bash
uv sync
uv run pytest -q
```

## Release

- Bump version: `uv version --bump patch` (or `minor`/`major`)
- Build: `uv build --no-sources`
- Upload: `uv publish`

Alternatively, use GitHub Actions with **Trusted Publishing** (see below).

## GitHub Actions (uv)

This repo includes a workflow that:
- installs uv
- builds the package with `uv build --no-sources`
- publishes to PyPI via **Trusted Publishing** when you push a tag like `v0.1.0`

To enable Trusted Publishing on PyPI, add your GitHub repo as a **Trusted Publisher** on the project settings.

## License

MIT
