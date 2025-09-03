from celery import chain, group, chord
from celery_context_headers import TaskSender
from .tasks import add, agg
from .context import trace_id_var, tenant_id_var, debug_var, current_headers

sender = TaskSender(current_headers)

def demo():
    # set per-request context
    trace_id_var.set("req-42")
    tenant_id_var.set("acme")
    debug_var.set({"trace": True})

    res1 = sender.delay(add, 2, 3)
    print("res1:", res1.get(timeout=10))

    res2 = sender.send(chain(add.s(1,2), add.s(3)))
    print("res2:", res2.get(timeout=10))

    res3 = sender.send(group(add.s(i, i) for i in range(3)))
    print("res3:", sorted(res3.get(timeout=10)))

    res4 = sender.send(chord(group(add.s(i, 1) for i in range(3)), body=agg.s()))
    print("res4:", res4.get(timeout=10))

if __name__ == "__main__":
    demo()
