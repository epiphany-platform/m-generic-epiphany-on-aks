import sys
import subprocess

from ._helpers import get_path, combine, load_yaml, dump_yaml, to_literal_scalar, udiff
from .plan import _extract_module_config, _diff_module_configs


FINAL_MODULE_STATE = '''
kind: state
{M_MODULE_SHORT}:
  status: applied
  config: |
'''


def _run_epicli_apply(v):
    try:
        config = load_yaml(v["config_file"])[v["M_MODULE_SHORT"]]["config"]

        with v["epiphany_file"].open("w") as stream:
            stream.write(config)

        command = " ".join([
            "epicli",
            "--auto-approve",
            "apply",
            "--file=" + str(v["epiphany_file"]),
            "--vault-password=" + "'asd'",
        ])

        rc = subprocess.run(command, shell=True).returncode

        return rc

    finally:
        v["epiphany_file"].unlink(missing_ok=True)


def _update_state_file(v):
    state = load_yaml(v["state_file"])

    state = combine(state, load_yaml(FINAL_MODULE_STATE.format(**v).strip()))

    config = load_yaml(v["config_file"])[v["M_MODULE_SHORT"]]["config"]

    state = combine(state, {
        v["M_MODULE_SHORT"]: {
            "config": to_literal_scalar(config),
        },
    })

    with v["state_file"].open("w") as stream:
        dump_yaml(state, stream=stream)


def main(variables={}):
    """Handle apply method."""

    # Compute paths
    v = variables
    v["shared_dir"] = get_path(v["M_SHARED"])
    v["module_dir"] = get_path(str(v["shared_dir"] / v["M_MODULE_SHORT"]))
    v["config_file"] = get_path(str(v["module_dir"] / v["M_CONFIG_NAME"]))
    v["state_file"] = get_path(str(v["shared_dir"] / v["M_STATE_FILE_NAME"]))
    v["epiphany_file"] = get_path(str(v["module_dir"] / "epiphany-config.yml")).resolve()

    # Create plan file required for apply method
    with (v["module_dir"] / "plan.diff").open("r") as stream:
        plan_diff = stream.read()

    extracted_config = _extract_module_config(v)

    current_diff = _diff_module_configs(v, extracted_config)

    if not (bool(plan_diff) and bool(current_diff) and plan_diff == current_diff):
        print("no changes to apply")
        return

    rc = _run_epicli_apply(v)
    if rc != 0:
        sys.exit(rc)

    _update_state_file(v)
