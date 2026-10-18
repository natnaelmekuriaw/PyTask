import argparse
import sys

from sqlalchemy.exc import SQLAlchemyError

from pytask_service.config import Settings
from pytask_service.db.engine import build_engine, check_connection


def main() -> int:
    parser = argparse.ArgumentParser(prog="pytask-service")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check-db", help="Check the database connection")
    args = parser.parse_args()

    if args.command == "check-db":
        try:
            engine = build_engine(Settings.from_env())
            try:
                check_connection(engine)
            finally:
                engine.dispose()
        except (ValueError, SQLAlchemyError) as exc:
            print(f"Database check failed: {exc}", file=sys.stderr)
            return 1
        print("Database connection OK")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
