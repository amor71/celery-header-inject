from __future__ import annotations

from typing import Any, Mapping, Optional, Callable, Dict, Iterable
from celery.canvas import Signature


HeadersProvider = Callable[[], Mapping[str, Any]]


def _merge_headers(existing: Optional[Mapping[str, Any]], new: Mapping[str, Any]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    if existing:
        merged.update(existing)
    if new:
        merged.update(new)
    return merged


def apply_headers(sig: Signature, headers: Mapping[str, Any]) -> Signature:
    """Shallow set of headers on a Signature (clone-safe)."""
    sig = sig.clone()
    sig.set(headers=_merge_headers(sig.options.get("headers"), headers))
    return sig


def deep_set_headers(sig: Signature, headers: Mapping[str, Any]) -> Signature:
    """Clone a Celery signature/canvas and set headers on it and all children.

    This recurses through chain/group/chord and link/error-link callbacks.
    """
    sig = sig.clone()
    # set on this node
    sig.set(headers=_merge_headers(sig.options.get("headers"), headers))

    # propagate to callback links
    for key in ("link", "link_error"):
        links: Optional[Iterable[Signature]] = sig.options.get(key)
        if links:
            sig.options[key] = [deep_set_headers(s, headers) for s in links]

    # propagate to children in canvas types (chain/group/chord)
    if hasattr(sig, "tasks"):  # chain, group, chord header 'tasks'
        sig.tasks = [deep_set_headers(s, headers) for s in sig.tasks]
    if hasattr(sig, "body") and sig.body is not None:  # chord callback
        sig.body = deep_set_headers(sig.body, headers)

    return sig


class TaskSender:
    """Attach per-request headers to any Signature/canvas, then apply_async().

    Example:
        sender = TaskSender(headers_provider=current_headers)
        result = sender.delay(my_task, 1, 2)  # like my_task.delay(1, 2)
        result = sender.send(my_task.s(1, 2), extra_headers={"trace_id": "abc"})
    """

    def __init__(self, headers_provider: HeadersProvider):
        self.headers_provider = headers_provider

    def with_headers(
        self,
        sig: Signature,
        extra_headers: Optional[Mapping[str, Any]] = None,
        deep: bool = True,
    ) -> Signature:
        base = dict(self.headers_provider() or {})
        if extra_headers:
            base.update(extra_headers)
        return deep_set_headers(sig, base) if deep else apply_headers(sig, base)

    def send(self, sig: Signature, *, extra_headers: Optional[Mapping[str, Any]] = None, **apply_async_kwargs):
        return self.with_headers(sig, extra_headers=extra_headers).apply_async(**apply_async_kwargs)

    def delay(self, task, *args, extra_headers: Optional[Mapping[str, Any]] = None, **kwargs):
        # NOTE: Celery's .delay() can't attach headers, so we use .s() + apply_async()
        return self.send(task.s(*args, **kwargs), extra_headers=extra_headers)
