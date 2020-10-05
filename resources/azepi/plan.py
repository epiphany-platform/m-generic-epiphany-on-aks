import sys
import pathlib

from ._helpers import get_path, load_yaml, udiff


def _extract_module_config(v):
    """Extract module config."""

    state = load_yaml(v["state_file"])

    try:
        config = state[v["M_MODULE_SHORT"]]["config"]
    except KeyError:
        config = ""

    return config


def _diff_module_configs(v, extracted_config):
    """Compute unified diff between module configs."""

    current_config = load_yaml(v["config_file"])[v["M_MODULE_SHORT"]]["config"]

    return udiff(extracted_config.strip(), current_config.strip()).strip()


def main(variables={}):
    """Handle plan method."""

    # Compute paths
    v = variables
    v["shared_dir"] = get_path(v["M_SHARED"])
    v["module_dir"] = get_path(str(v["shared_dir"] / v["M_MODULE_SHORT"]))
    v["config_file"] = get_path(str(v["module_dir"] / v["M_CONFIG_NAME"]))
    v["state_file"] = get_path(str(v["shared_dir"] / v["M_STATE_FILE_NAME"]))

    extracted_config = _extract_module_config(v)

    config_diff = _diff_module_configs(v, extracted_config)

    # Create plan file required for apply method
    with (v["module_dir"] / "plan.diff").open("w") as stream:
        stream.write(config_diff)

    if config_diff:
        print(config_diff, file=sys.stdout)
