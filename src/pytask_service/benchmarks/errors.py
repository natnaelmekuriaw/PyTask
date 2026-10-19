class BenchmarkFailure(RuntimeError):
    def __init__(self, code: str, *, retained_schema: str | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.retained_schema = retained_schema
