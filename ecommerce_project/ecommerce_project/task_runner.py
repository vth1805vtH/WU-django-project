import re
import socket
import threading
import uuid

_in_memory = {}
_lock = threading.Lock()
_redis_available = None


def _check_redis():
    global _redis_available
    if _redis_available is not None:
        return _redis_available

    try:
        from django.conf import settings
        url = getattr(settings, 'CELERY_BROKER_URL', '')
        if not url or not url.startswith('redis'):
            _redis_available = False
            return False

        match = re.search(r'redis://([^:]+):(\d+)', url)
        if not match:
            _redis_available = False
            return False

        host, port = match.group(1), int(match.group(2))
        with socket.create_connection((host, port), timeout=0.5):
            _redis_available = True
            return True
    except Exception:
        _redis_available = False
        return False


def _thread_run(target_fn, *args, **kwargs):
    task_id = str(uuid.uuid4())
    with _lock:
        _in_memory[task_id] = {'status': 'PENDING'}

    def _wrapper():
        try:
            with _lock:
                _in_memory[task_id]['status'] = 'STARTED'
            result = target_fn(*args, **kwargs)
            with _lock:
                _in_memory[task_id].update({'status': 'SUCCESS', 'result': result})
        except Exception as e:
            with _lock:
                _in_memory[task_id].update({'status': 'FAILURE', 'error': str(e)})

    threading.Thread(target=_wrapper, daemon=True).start()
    return task_id


def submit(celery_task, sync_fn, *args, **kwargs):
    if _check_redis():
        try:
            result = celery_task.delay(*args, **kwargs)
            return result.id, True
        except Exception:
            pass
    task_id = _thread_run(sync_fn, *args, **kwargs)
    return task_id, False


def get_status(task_id):
    with _lock:
        entry = _in_memory.get(task_id)

    if entry is not None:
        return dict(entry)

    try:
        from celery.result import AsyncResult
        from .celery import app
        result = AsyncResult(task_id, app=app)
        if result.ready():
            if result.successful():
                return {'status': 'SUCCESS', 'result': result.result}
            return {'status': 'FAILURE', 'error': str(result.result)}
        return {'status': result.state}
    except Exception:
        pass

    return {'status': 'FAILURE', 'error': 'Unknown task'}


def redis_available():
    return _check_redis()
