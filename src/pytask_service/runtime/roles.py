from enum import StrEnum


class Role(StrEnum):
    API = "api"
    WORKER = "worker"
    SCHEDULER = "scheduler"
    MIGRATE = "migrate"
    CLI = "cli"
    CHECK = "check"
    PROBE = "probe"
