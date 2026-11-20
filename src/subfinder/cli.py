"""The entry point: every command starts here. This file only reads the command line and hands over.

`demo` needs no token and sends nothing. `run` makes one real model call, so it only prints its plan unless given
`--yes`.
"""

from __future__ import annotations

import argparse
import sys

from subfinder.lib.api.commands import cmd_run
from subfinder.lib.demo.walkthrough import run_walkthrough
from subfinder.lib.hooks.commands import cmd_check
from subfinder.lib.mcp_server.commands import cmd_serve
from subfinder.lib.mcp_server.http import CONFIG as HTTP
from subfinder.lib.statement.workbook import reset_workbook


def _cmd_demo(_: argparse.Namespace) -> int:
    run_walkthrough()
    return 0


def _cmd_reset(_: argparse.Namespace) -> int:
    reset_workbook()
    print("Forgot the current run.")
    return 0


def main() -> None:
    """Parse the command line and run a command."""
    parser = argparse.ArgumentParser(prog="subfinder", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("demo", help="walk through every type with a scripted model (free)").set_defaults(run=_cmd_demo)

    real_run = commands.add_parser("run", help="run the whole job, cleaning names with GitHub Models")
    real_run.add_argument("--yes", action="store_true", help="make the real call")
    real_run.set_defaults(run=lambda args: cmd_run(args.yes))

    commands.add_parser("reset", help="forget the current run").set_defaults(run=_cmd_reset)

    checker = commands.add_parser("check", help="run the checks against the current run and say what they found")
    checker.set_defaults(run=lambda _: cmd_check())

    server = commands.add_parser("serve-http", help="serve the read tools over HTTP on this machine")
    server.add_argument("--port", type=int, default=HTTP.default_port)
    server.add_argument("--public-host", help="the host name of the tunnel in front of this server")
    server.add_argument("--no-auth", action="store_true", help="serve with no token: for made-up data only")
    server.set_defaults(run=lambda args: cmd_serve(args.port, args.public_host, args.no_auth))

    args = parser.parse_args()
    sys.exit(args.run(args))
