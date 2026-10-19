from contextlib import nullcontext


class Connection:
    def __init__(self) -> None:
        self.statements: list[object] = []

    def __enter__(self) -> "Connection":
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def begin(self) -> object:
        return nullcontext()

    def exec_driver_sql(self, statement: str) -> None:
        self.statements.append(statement)

    def execute(self, statement: object) -> None:
        self.statements.append(statement)


class Engine:
    def __init__(self) -> None:
        self.connection = Connection()
        self.disposed = False
        self.connected = False

    def connect(self) -> Connection:
        self.connected = True
        return self.connection

    def dispose(self) -> None:
        self.disposed = True
