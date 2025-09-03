from contextvars import ContextVar

trace_id_var = ContextVar("trace_id", default=None)
tenant_id_var = ContextVar("tenant_id", default=None)
debug_var    = ContextVar("debug", default=None)

def current_headers() -> dict:
    h = {}
    if (v := trace_id_var.get()): h["trace_id"] = v
    if (v := tenant_id_var.get()): h["tenant_id"] = v
    if (v := debug_var.get()): h["debug"] = v
    return h
