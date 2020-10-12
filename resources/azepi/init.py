"""Implementation of the "init" method."""

import sys
from ._helpers import (get_path, combine, dictify, undictify,
                       load_yaml, dump_yaml, dump_yaml_into_str, to_literal_scalar)


# The standard "minimal-cluster-config.yml" is not used here because
# it contains too many extra documents
MINIMAL_EPIPHANY_CLUSTER = '''
kind: epiphany-cluster
title: Epiphany cluster Config
name: TO_BE_SET
provider: any
specification:
  name: TO_BE_SET
  admin_user:
    name: operations
    key_path: TO_BE_SET
  cloud:
    k8s_as_cloud_service: true
  components:
    repository:
      count: 1
    kubernetes_master:
      count: 0
    kubernetes_node:
      count: 0
    logging:
      count: 0
    monitoring:
      count: 0
    kafka:
      count: 0
    postgresql:
      count: 1
    load_balancer:
      count: 0
    rabbitmq:
      count: 0
'''

# Extend feature mapping of repository to enable applications
MINIMAL_FEATURE_MAPPING = '''
kind: configuration/feature-mapping
title: Feature mapping to roles
name: TO_BE_SET
provider: any
specification:
  roles_mapping:
    repository:
      - repository
      - image-registry
      - firewall
      - filebeat
      - node-exporter
      - applications
'''

# Original one seems to be incorrect:
# https://github.com/epiphany-platform/epiphany/issues/1743
VIRTUAL_MACHINE_TEMPLATE = '''
kind: infrastructure/machine
name: TO_BE_SET
provider: any
specification:
  hostname: TO_BE_SET
  ip: TO_BE_SET
'''

INITIAL_MODULE_STATE = '''
kind: state
{M_MODULE_SHORT}:
  status: initialized
'''

INITIAL_MODULE_CONFIG = '''
kind: {M_MODULE_SHORT}-config
{M_MODULE_SHORT}:
  vault_password: "asd"
'''


def _get_enabled_components(cluster):
    """Get all components with non-zero "count"."""

    return [
        (key, value)
        for key, value in cluster["specification"]["components"].items()
        if int(value["count"]) > 0
    ]


def _get_dummy_machines(cluster):
    """Generate dummy virtual machine documents."""

    count = sum(
        value["count"]
        for _, value in _get_enabled_components(cluster)
    )

    return [
        combine(load_yaml(VIRTUAL_MACHINE_TEMPLATE), {
            "name": "default-vm-" + str(index + 1),
        })
        for index in range(count)
    ]


def _process_cluster(v):
    """Process the main cluster document."""

    return combine(load_yaml(MINIMAL_EPIPHANY_CLUSTER), {
        "name": v["M_MODULE_SHORT"],
        "provider": "any",
        "specification": {
            "name": v["M_MODULE_SHORT"],
            "admin_user": {
                "key_path": str(v["shared_dir"] / v["VMS_RSA_FILENAME"]),
            },
        },
    })


def _process_feature_mapping(v):
    """Process feature mapping (enable applications)."""

    return combine(load_yaml(MINIMAL_FEATURE_MAPPING), {
        "name": v["M_MODULE_SHORT"],
        "provider": "any",
    })


def _process_machines(v, cluster):
    """Process virtual machines."""

    def read_vms_from_state_file():
        state = load_yaml(v["state_file"])["azbi"]
        output = state["output"]

        vm_names = output["vm_names.value"]

        if state["use_public_ip"]:
            vm_ips = output["public_ips.value"]
        else:
            vm_ips = output["private_ips.value"]

        return zip(vm_names, vm_ips)

    def derive_machines(vms):
        return [
            combine(load_yaml(VIRTUAL_MACHINE_TEMPLATE), {
                "name": "default-" + vm_name,
                "provider": "any",
                "specification": {
                    "hostname": vm_name,
                    "ip": vm_ip,
                },
            })
            for vm_name, vm_ip in vms
        ]

    def assign_machines_to_components(machines, cluster):
        number_of_required_vms = sum(
            int(value["count"])
            for _, value in _get_enabled_components(cluster)
        )

        if number_of_required_vms > len(machines):
            raise Exception("not enough vms available")

        # Convert virtual machine list to iterator
        machines = iter(machines)

        return combine(cluster, {
            "specification": {
                "components": {
                    key: {
                        "machines": [
                            next(machines)["name"]
                            for _ in range(int(value["count"]))
                        ],
                    }
                    for key, value in _get_enabled_components(cluster)
                },
            },
        })

    try:
        # Read data from the state file
        vms = read_vms_from_state_file()
        machines = derive_machines(vms)
    except (FileNotFoundError, KeyError):
        # Fallback to dummy values if there is no state to read
        vms = []
        machines = _get_dummy_machines(cluster)

    cluster = assign_machines_to_components(machines, cluster)

    return machines, cluster


def _process_components(v, cluster):
    """Process component defaults."""

    return [
        combine(load_yaml(v["template_dir"] / "configuration" / (key + ".yml")), {
            "provider": "any",
        })
        for key, _ in _get_enabled_components(cluster)
    ]


def _process_applications(v):
    """Process application defaults."""

    template = load_yaml(
        v["template_dir"] / "configuration" / "applications.yml")

    # Add provider key
    document = combine(template, {
        "provider": "any",
    })

    # Convert list-based dictionary to real one (makes merging possible)
    applications = dictify(
        document["specification"]["applications"])

    # Make sure user gets defaults appropriate for cloud Kuberentes
    applications = combine(applications, {
        key: {
            "use_local_image_registry": False,
        }
        for key, value in applications.items()
        if "use_local_image_registry" in value
    })

    return combine(document, {
        "specification": {
            # Convert-back to list-based dictionary
            "applications": undictify(applications),
        },
    })


def _update_state_file(v):
    """Add module's state to the state file."""

    try:
        state = load_yaml(v["state_file"])
    except FileNotFoundError:
        state = {}

    state = combine(state, load_yaml(INITIAL_MODULE_STATE.format(**v).strip()))

    with v["state_file"].open("w") as stream:
        dump_yaml(state, stream=stream)


def _output_data(v, documents):
    """Save and display generated config."""

    v["module_dir"].mkdir(parents=True, exist_ok=True)

    if v["config_file"].exists():
        v["config_file"].rename(v["backup_file"])

    config = load_yaml(INITIAL_MODULE_CONFIG.format(**v).strip())

    output = dump_yaml_into_str(documents)

    config = combine(config, {
        v["M_MODULE_SHORT"]: {
            "config": to_literal_scalar(output),
        },
    })

    with v["config_file"].open("w") as stream:
        dump_yaml(config, stream=stream)

    dump_yaml(config, stream=sys.stdout)


def main(variables={}):
    """Handle init method."""

    # Compute paths
    v = variables
    v["shared_dir"] = get_path(v["M_SHARED"])
    v["template_dir"] = get_path(v["M_TEMPLATES"])

    v["module_dir"] = get_path(
        str(v["shared_dir"] / v["M_MODULE_SHORT"]))

    v["config_file"] = get_path(
        str(v["module_dir"] / v["M_CONFIG_NAME"]))

    v["state_file"] = get_path(
        str(v["shared_dir"] / v["M_STATE_FILE_NAME"]))

    v["backup_file"] = get_path(
        str(v["module_dir"] / (v["M_CONFIG_NAME"] + ".backup")))

    cluster = _process_cluster(v)

    mapping = _process_feature_mapping(v)

    machines, cluster = _process_machines(v, cluster)

    components = _process_components(v, cluster)

    applications = _process_applications(v)

    _output_data(v, [cluster] + [mapping]
                              + machines
                              + components
                              + [applications])
    _update_state_file(v)
