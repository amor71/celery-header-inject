from fastapi import FastAPI, Request
import uuid
from contextvars import ContextVar
from celery_context_headers import TaskSender

# app-level contextvars
trace_id_var = ContextVar("trace_id", default=None)
tenant_id_var = ContextVar("tenant_id", default=None)

def current_headers():
    h = {}
    if (v := trace_id_var.get()): h["trace_id"] = v
    if (v := tenant_id_var.get()): h["tenant_id"] = v
    return h

sender = TaskSender(current_headers)
app = FastAPI()

@app.middleware("http")
async def add_contextvars(request: Request, call_next):
    trace_id_var.set(request.headers.get("x-trace-id") or str(uuid.uuid4()))
    tenant_id_var.set(request.headers.get("x-tenant-id"))
    return await call_next(request)
