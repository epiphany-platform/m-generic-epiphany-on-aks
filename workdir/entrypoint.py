import os
import sys
import argparse
import azepi


def _add_metadata_parser(subparsers):
    parser = subparsers.add_parser("metadata")
    parser.set_defaults(handler=azepi.metadata.main)


def _add_init_parser(subparsers):
    parser = subparsers.add_parser("init")
    parser.add_argument("variables", metavar='KEY=VALUE', type=str, nargs="+")
    parser.set_defaults(handler=azepi.init.main)


def _add_plan_parser(subparsers):
    parser = subparsers.add_parser("plan")
    parser.set_defaults(handler=azepi.plan.main)


def _add_apply_parser(subparsers):
    parser = subparsers.add_parser("apply")
    parser.set_defaults(handler=azepi.apply.main)


def _add_destroy_plan_parser(subparsers):
    parser = subparsers.add_parser("destroy-plan")
    parser.set_defaults(handler=azepi.destroy_plan.main)


def _add_destroy_parser(subparsers):
    parser = subparsers.add_parser("destroy")
    parser.set_defaults(handler=azepi.destroy.main)


def main():
    """Module's entrypoint"""

    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="command")
    _add_metadata_parser(subparsers)
    _add_init_parser(subparsers)
    _add_plan_parser(subparsers)
    _add_apply_parser(subparsers)
    _add_destroy_plan_parser(subparsers)
    _add_destroy_parser(subparsers)

    arguments = parser.parse_args()

    # Parse values both from environment variables and from command line
    variables = dict(
        [
            (key, value)
            for key, value in os.environ.items()
            if key.startswith("M_")
        ] + [
            variable.split("=", maxsplit=1)
            for variable in getattr(arguments, "variables", [])
            if "=" in variable
        ]
    )

    return arguments.handler(variables)


if __name__ == "__main__":
    sys.exit(main())
