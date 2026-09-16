"""Dispatch the public brain commands from the caller's working directory."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.index.brain_lint import brain_lint
from tools.index.data_directory_not_found_error import DataDirectoryNotFoundError
from tools.index.doctor_report import doctor_report
from tools.index.find_data_directory import find_data_directory
from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.load_syntopica_config import load_syntopica_config


def brain_cli(argv: list[str] | None = None) -> int:
    """Resolve instance selection once, preserving subcommand arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", metavar="PATH")
    parser.add_argument("command", choices=("index", "graph", "lint", "doctor", "find"))
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        root = find_data_directory(args.data, os.environ, Path.cwd())
        if args.command in {"lint", "doctor"} and args.arguments:
            parser.error(f"{args.command} does not accept additional arguments")
        if args.command == "doctor":
            return doctor_report(root, os.environ)
        config = load_syntopica_config(root, os.environ)
        if args.command == "lint":
            return brain_lint(config)
        script = Path(__file__).resolve().parents[1] / args.command / "build.py"
        return subprocess.run(
            [sys.executable, str(script), "--data", str(root), *args.arguments], check=False
        ).returncode
    except (DataDirectoryNotFoundError, InvalidSyntopicaConfigError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(brain_cli())
