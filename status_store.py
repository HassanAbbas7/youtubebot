from threading import Lock


# Simple in-memory status store. For production replace with DB or redis.
_store = {}
_lock = Lock()




def set_status(job_id, payload):
    with _lock:
        _store[job_id] = payload




def get_status(job_id):
    with _lock:
        return _store.get(job_id)




def list_statuses():
    with _lock:
        return dict(_store)