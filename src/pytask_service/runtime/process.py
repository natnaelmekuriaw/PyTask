import os

from pytask_service.runtime.command import ProcessCommand


def replace_process(command: ProcessCommand) -> None:
    os.execv(command.argv[0], command.argv)
