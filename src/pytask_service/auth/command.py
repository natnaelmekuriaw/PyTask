import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from pytask_service.auth.files import read_manifest_file, write_key_files
from pytask_service.auth.issuance import issue_key
from pytask_service.auth.permissions import Permission


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m pytask_service.auth")
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser(
        "generate", help="Write a new token and digest manifest"
    )
    generate.add_argument("--id", required=True, dest="key_id")
    generate.add_argument(
        "--scope", action="append", choices=list(Permission), required=True
    )
    generate.add_argument("--token-file", type=Path, required=True)
    generate.add_argument("--manifest", type=Path, required=True)
    inspect = commands.add_parser(
        "inspect", help="Validate a manifest without showing digests"
    )
    inspect.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            if len(set(args.scope)) != len(args.scope):
                raise ValueError("Specify each permission only once")
            issued = issue_key(
                args.key_id, frozenset(Permission(item) for item in args.scope)
            )
            write_key_files(issued, args.token_file, args.manifest)
            print("Created token and manifest files")
        else:
            keys = read_manifest_file(args.manifest)
            print(
                json.dumps(
                    {
                        "version": 1,
                        "keys": [
                            {"id": key.key_id, "scopes": sorted(key.permissions)}
                            for key in keys
                        ],
                    }
                )
            )
    except ValueError as error:
        print(f"Key command failed: {error}", file=sys.stderr)
        return 1
    return 0
