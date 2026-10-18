import os
import socket
from uuid import uuid4


def new_worker_id() -> str:
    host = socket.gethostname()[:64]
    return f"{host}:{os.getpid()}:{uuid4().hex[:12]}"
