"""Implementation of the "plan" method."""

import sys
from ._helpers import get_path, load_yaml, dump_yaml_into_str, sorted_dict, udiff


def _diff_module_configs(v):
    """Compute unified diff between state and module config."""

    state = load_yaml(v["state_file"])[v["M_MODULE_SHORT"]]

    # Remove known keys that are not parts of the config
    for key_to_remove in {"status", "output"}:
        if key_to_remove in state:
            del state[key_to_remove]

    config = load_yaml(v["config_file"])[v["M_MODULE_SHORT"]]

    return udiff(
        dump_yaml_into_str(sorted_dict(state)).strip(),
        dump_yaml_into_str(sorted_dict(config)).strip(),
    ).strip()


def main(variables={}):
    """Handle plan method."""

    # Compute paths
    v = variables
    v["shared_dir"] = get_path(v["M_SHARED"])

    v["module_dir"] = get_path(
        str(v["shared_dir"] / v["M_MODULE_SHORT"]))

    v["config_file"] = get_path(
        str(v["module_dir"] / v["M_CONFIG_NAME"]))

    v["state_file"] = get_path(
        str(v["shared_dir"] / v["M_STATE_FILE_NAME"]))

    config_diff = _diff_module_configs(v)

    # Create plan file required for apply method
    with (v["module_dir"] / "plan.diff").open("w") as stream:
        stream.write(config_diff)

    if config_diff:
        print(config_diff, file=sys.stdout)
