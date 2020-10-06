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
      machines: []
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
      machines: []
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

# Original one seems to be incorrect (05 Oct 2020)
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
'''


def _get_enabled_components(cluster):
    enabled_components = [
        (key, value)
        for key, value in cluster["specification"]["components"].items()
        if int(value["count"]) > 0
    ]
    return enabled_components


def _get_dummy_machines(count):
    machine_template = load_yaml(VIRTUAL_MACHINE_TEMPLATE)

    return [
        combine(machine_template, {
            "name": "default-vm-" + str(index + 1),
        })
        for index in range(count)
    ]


def _process_cluster(v):
    """Process the main cluster document."""

    cluster_template = load_yaml(MINIMAL_EPIPHANY_CLUSTER)

    cluster = combine(cluster_template, {
        "name": v["M_MODULE_SHORT"],
        "provider": "any",
        "specification": {
            "name": v["M_MODULE_SHORT"],
            "admin_user": {
                "key_path": str(v["shared_dir"] / v["VMS_RSA_FILENAME"]),
            },
        },
    })

    return cluster


def _process_feature_mapping(v):
    """Process feature mapping (enable applications)."""

    mapping_template = load_yaml(MINIMAL_FEATURE_MAPPING)

    mapping = combine(mapping_template, {
        "name": v["M_MODULE_SHORT"],
        "provider": "any",
    })

    return mapping


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

        vms = zip(vm_names, vm_ips)

        return vms

    def derive_machines(vms):
        machine_template = load_yaml(VIRTUAL_MACHINE_TEMPLATE)

        machines = [
            combine(machine_template, {
                "name": "default-" + vm_name,
                "provider": "any",
                "specification": {
                    "hostname": vm_name,
                    "ip": vm_ip,
                },
            })
            for vm_name, vm_ip in vms
        ]

        return machines

    def assign_machines_to_components(machines, cluster):
        number_of_required_vms = sum(
            int(value["count"])
            for _, value in _get_enabled_components(cluster)
        )

        if number_of_required_vms > len(machines):
            raise Exception("not enough vms available")

        # Convert virtual machine list to iterator
        machines = iter(machines)

        cluster = combine(cluster, {
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

        return cluster

    try:
        # Read data from the state file
        vms = read_vms_from_state_file()
        machines = derive_machines(vms)
    except (FileNotFoundError, KeyError):
        # Fallback to dummy values if there is no state to read
        vms = []
        # "2" is in sync with the INITIAL_MODULE_CONFIG
        machines = _get_dummy_machines(2)

    cluster = assign_machines_to_components(machines, cluster)

    return machines, cluster


def _process_components(v, cluster):
    """Process component defaults."""

    components = [
        combine(load_yaml(v["template_dir"] / "configuration" / (key + ".yml")), {
            "provider": "any",
        })
        for key, _ in _get_enabled_components(cluster)
    ]

    return components


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

    document = combine(document, {
        "specification": {
            # Convert-back to list-based dictionary
            "applications": undictify(applications),
        },
    })

    return document


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
