from celery.canvas import chain, group
from celery_context_headers import apply_headers, deep_set_headers, TaskSender

def test_apply_headers_shallow():
    from celery import shared_task

    # minimal dummy signature via group of nothing as a stand-in
    # but we can create any signature using s()
    from celery import Celery
    app = Celery('x', broker='memory://', backend='cache+memory://')
    @app.task
    def t(a): return a

    s = t.s(1)
    s2 = apply_headers(s, {"trace_id": "abc"})
    assert s.options.get("headers") is None
    assert s2.options["headers"]["trace_id"] == "abc"

def test_deep_set_headers_on_canvas():
    from celery import Celery
    app = Celery('x', broker='memory://', backend='cache+memory://')
    @app.task
    def add(x, y): return x + y

    c = chain(add.s(1,2), add.s(3))
    g = group(add.s(i, i) for i in range(3))
    canvas = chain(c, g)

    canvas2 = deep_set_headers(canvas, {"tenant": "acme"})
    # chain -> tasks list
    assert all(s.options.get("headers", {}).get("tenant") == "acme" for s in canvas2.tasks)
    # inner group also gets headers
    inner_group = canvas2.tasks[-1]
    assert all(s.options.get("headers", {}).get("tenant") == "acme" for s in inner_group.tasks)

def test_task_sender_delay_like():
    calls = []
    def provider(): return {"x": "y"}
    sender = TaskSender(provider)

    from celery import Celery
    app = Celery('x', broker='memory://', backend='cache+memory://')
    @app.task(bind=True)
    def t(self, a): 
        calls.append(self.request.headers)
        return a

    r = sender.delay(t, 5)
    r.get(timeout=3)
    assert calls and calls[0]["x"] == "y"
