"""Implementation of the "apply" method."""

import os
import subprocess
import textwrap
from ._helpers import combine, dump_yaml, get_path, load_yaml, q_kind, select
from .plan import _diff_module_configs


FINAL_MODULE_STATE = '''
kind: state
{M_MODULE_SHORT}:
  status: applied
'''


def _extract_kubeconfig(v):
    """Extract kubeconfig from state and save it in a file."""

    state = load_yaml(v["state_file"])

    kubeconfig = state["azks"]["output"]["kubeconfig.value"]

    v["kubeconfig_file"].parent.mkdir(parents=True, exist_ok=True)

    with v["kubeconfig_file"].open("w") as stream:
        stream.write(kubeconfig)


def _run_epicli_apply(v):
    """Deploy Epiphany."""

    try:
        module_config = load_yaml(v["config_file"])[v["M_MODULE_SHORT"]]

        epiphany_config = module_config["config"]

        with v["epiphany_file"].open("w") as stream:
            stream.write(epiphany_config)

        command = " ".join([
            "epicli",
            "--auto-approve",
            "apply",
            "--file='{}'".format(v["epiphany_file"]),
            "--vault-password='{:s}'".format(module_config["vault_password"]),
        ])

        subprocess.run(command, shell=True, check=True)

    finally:
        if v["epiphany_file"].exists():
            v["epiphany_file"].unlink()


def _ensure_ssh_key_permissions(v):
    """Apply SSH key permissions workaround for Docker on Windows."""

    module_config = load_yaml(v["config_file"])[v["M_MODULE_SHORT"]]

    epiphany_config_docs = load_yaml(module_config["config"])

    cluster = select(epiphany_config_docs,
                     q_kind("epiphany-cluster"),
                     exactly=1)

    spec_key_path = get_path(
        cluster["specification"]["admin_user"]["key_path"])

    shared_dir_key_path = v["shared_dir"] / "vms_rsa"

    command = textwrap.dedent(f'''
        set -e
        if [ ! -f "{spec_key_path}" ]; then
            echo "File {spec_key_path} not found, will copy {shared_dir_key_path}"
            cp --verbose {shared_dir_key_path}* {spec_key_path.parent}
        fi
        if [ $(stat -c '%a' {spec_key_path}) != '600' ]; then
            echo "Unexpected permissions on file {spec_key_path}, will correct"
            chmod 600 {spec_key_path}
        fi
    ''').strip()

    result = subprocess.run(command, shell=True, check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    if len(result.stdout) > 0:
        print(result.stdout.decode("utf-8"))


def _update_state_file(v):
    """Make sure state is up to date."""

    config = load_yaml(v["config_file"])[v["M_MODULE_SHORT"]]

    state = load_yaml(v["state_file"])

    state = combine(state, load_yaml(FINAL_MODULE_STATE.format(**v).strip()))

    state = combine(state, {
        v["M_MODULE_SHORT"]: config,
    })

    with v["state_file"].open("w") as stream:
        dump_yaml(state, stream=stream)


def main(variables={}):
    """Handle apply method."""

    # Compute paths
    v = variables
    v["shared_dir"] = get_path(v["M_SHARED"])

    v["module_dir"] = get_path(
        str(v["shared_dir"] / v["M_MODULE_SHORT"]))

    v["config_file"] = get_path(
        str(v["module_dir"] / v["M_CONFIG_NAME"]))

    v["state_file"] = get_path(
        str(v["shared_dir"] / v["M_STATE_FILE_NAME"]))

    v["epiphany_file"] = get_path(
        str(v["module_dir"] / "epiphany-config.yml"))

    v["kubeconfig_file"] = get_path(
        str(v["shared_dir"] / "build" / v["M_MODULE_SHORT"] / "kubeconfig"))

    # Create plan file required for apply method
    with (v["module_dir"] / "plan.diff").open("r") as stream:
        plan_diff = stream.read()

    current_diff = _diff_module_configs(v)

    if not (bool(plan_diff) and bool(current_diff) and plan_diff == current_diff):
        print("no changes to apply")
        return

    print(os.environ, "\n")

    _extract_kubeconfig(v)

    _ensure_ssh_key_permissions(v)

    _run_epicli_apply(v)

    _update_state_file(v)
