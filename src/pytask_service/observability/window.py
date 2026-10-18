from dataclasses import dataclass

DEFAULT_WINDOW_SECONDS = 3600
MIN_WINDOW_SECONDS = 60
MAX_WINDOW_SECONDS = 7 * 24 * 60 * 60


@dataclass(frozen=True, slots=True)
class ObservationWindow:
    seconds: int = DEFAULT_WINDOW_SECONDS

    def __post_init__(self) -> None:
        if type(self.seconds) is not int or not (
            MIN_WINDOW_SECONDS <= self.seconds <= MAX_WINDOW_SECONDS
        ):
            raise ValueError("window_seconds must be an integer from 60 to 604800")
