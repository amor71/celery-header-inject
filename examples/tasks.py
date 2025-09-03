from celery import Celery

app = Celery("proj", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0")

@app.task(bind=True)
def add(self, x, y):
    hdrs = self.request.headers or {}
    if hdrs.get("debug", {}).get("trace"):
        print(f"[trace {hdrs.get('trace_id')}] add({x},{y})")
    return x + y

@app.task(bind=True)
def agg(self, values):
    return sum(values)
