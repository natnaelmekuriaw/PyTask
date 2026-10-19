import hashlib
from time import sleep

from pytask_service.registry import TaskRegistry

registry = TaskRegistry()


def noop(index: int) -> int:
    return index


def wait(index: int, milliseconds: int) -> int:
    if not 0 <= milliseconds <= 1000:
        raise ValueError("Sleep workload is limited to 1000 milliseconds")
    sleep(milliseconds / 1000)
    return index


def checksum(index: int, iterations: int) -> str:
    if not 1 <= iterations <= 1000000:
        raise ValueError("Checksum workload iterations are outside the supported range")
    value = str(index).encode("ascii")
    for _ in range(iterations):
        value = hashlib.sha256(value).digest()
    return value.hex()


registry.register("benchmark.noop", noop)
registry.register("benchmark.sleep", wait)
registry.register("benchmark.checksum", checksum)
