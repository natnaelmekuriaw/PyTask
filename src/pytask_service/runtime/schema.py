from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.util import CommandError

from pytask_service.runtime.paths import RuntimePaths


class RuntimeFailure(RuntimeError):
    pass


def expected_heads(paths: RuntimePaths) -> frozenset[str]:
    try:
        config = Config(str(paths.alembic_config))
        heads = frozenset(ScriptDirectory.from_config(config).get_heads())
    except (OSError, CommandError):
        raise RuntimeFailure(
            "Migration scripts are unavailable; check the image and configuration"
        ) from None
    if not heads:
        raise RuntimeFailure("The image contains no migration heads")
    return heads
