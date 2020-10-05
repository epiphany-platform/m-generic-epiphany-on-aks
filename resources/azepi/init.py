import io
import sys

from ._helpers import get_path, combine, dictify, undictify, load_yaml, dump_yaml, to_literal_scalar


# The standard "minimal-cluster-config.yml" is not used here because
# it contains too many extra documents. The "null" and "[]" should be
# replaced with correct values.
MINIMAL_EPIPHANY_CLUSTER = '''
kind: epiphany-cluster
title: Epiphany cluster Config
name: null
provider: any
specification:
  name: null
  admin_user:
    name: operations
    key_path: null
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
  config: |
'''


def _get_enabled_components(epiphany_cluster):
    enabled_components = [
        (key, value)
        for key, value in epiphany_cluster["specification"]["components"].items()
        if int(value["count"]) > 0
    ]
    return enabled_components


def _get_dummy_virtual_machines(v, count):
    virtual_machine_template = load_yaml(VIRTUAL_MACHINE_TEMPLATE)

    return [
        combine(virtual_machine_template, {
            "name": "default-vm-" + str(index + 1),
        })
        for index in range(count)
    ]


def _process_epiphany_cluster(v):
    """Process the main cluster document."""

    epiphany_cluster_template = load_yaml(MINIMAL_EPIPHANY_CLUSTER)

    epiphany_cluster = combine(epiphany_cluster_template, {
        "name": v["M_MODULE_SHORT"],
        "provider": "any",
        "specification": {
            "name": v["M_MODULE_SHORT"],
            "admin_user": {
                "key_path": str(v["shared_dir"] / v["VMS_RSA_FILENAME"]),
            },
        },
    })

    return epiphany_cluster


def _process_virtual_machines(v, epiphany_cluster):
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

    def derive_virtual_machines(vms):
        virtual_machine_template = load_yaml(VIRTUAL_MACHINE_TEMPLATE)

        virtual_machines = [
            combine(virtual_machine_template, {
                "name": "default-" + vm_name,
                "provider": "any",
                "specification": {
                    "hostname": vm_name,
                    "ip": vm_ip,
                },
            })
            for vm_name, vm_ip in vms
        ]

        return virtual_machines

    def assign_virtual_machines_to_components(virtual_machines, epiphany_cluster):
        number_of_required_vms = sum(
            int(value["count"])
            for _, value in _get_enabled_components(epiphany_cluster)
        )

        if number_of_required_vms > len(virtual_machines):
            raise Exception("not enough vms available")

        # Convert virtual machine list to iterator
        virtual_machines = iter(virtual_machines)

        epiphany_cluster = combine(epiphany_cluster, {
            "specification": {
                "components": {
                    key: {
                        "machines": [
                            next(virtual_machines)["name"]
                            for _ in range(int(value["count"]))
                        ],
                    }
                    for key, value in _get_enabled_components(epiphany_cluster)
                },
            },
        })

        return epiphany_cluster

    try:
        # Read data from the state file
        vms = read_vms_from_state_file()
        virtual_machines = derive_virtual_machines(vms)
    except (FileNotFoundError, KeyError):
        # Fallback to dummy values if there is no state to read
        vms = []
        virtual_machines = _get_dummy_virtual_machines(v, 4)

    epiphany_cluster = assign_virtual_machines_to_components(virtual_machines, epiphany_cluster)

    return virtual_machines, epiphany_cluster


def _process_components(v, epiphany_cluster):
    """Process component defaults."""

    components = [
        combine(load_yaml(v["template_dir"] / "configuration" / (key + ".yml")), {
            "provider": "any",
        })
        for key, _ in _get_enabled_components(epiphany_cluster)
    ]

    return components


def _process_applications(v):
    """Process application defaults."""

    applications_template = load_yaml(v["template_dir"] / "configuration" / "applications.yml")

    # Add provider key
    applications_template = combine(applications_template, {
        "provider": "any",
    })

    # Convert list-based dictionary to real one (makes merging possible)
    applications = dictify(applications_template["specification"]["applications"])

    # Make sure user gets defaults appropriate for cloud Kuberentes
    applications = combine(applications, {
        key: {
            "use_local_image_registry": False,
        }
        for key, value in applications.items()
        if "use_local_image_registry" in value
    })

    applications = combine(applications_template, {
        "specification": {
            "applications": undictify(applications),  # convert-back to list-based dictionary
        },
    })

    return applications


def _update_state_file(v):
    """Add module's state to the state file."""

    try:
        state = load_yaml(v["state_file"])
    except FileNotFoundError:
        state = {}

    try:
        # Make sure old state is completely deleted
        del state[v["M_MODULE_SHORT"]]
    except KeyError:
        pass

    state = combine(state, load_yaml(INITIAL_MODULE_STATE.format(**v).strip()))

    with v["state_file"].open("w") as stream:
        dump_yaml(state, stream=stream)


def _output_data(v, documents):
    """Save and display generated config."""

    try:
        stream = io.StringIO()
        dump_yaml(documents, stream=stream)
        stdout = stream.getvalue()
    finally:
        stream.close()

    v["module_dir"].mkdir(parents=True, exist_ok=True)

    if v["config_file"].exists():
        v["config_file"].rename(v["backup_file"])

    config = load_yaml(INITIAL_MODULE_CONFIG.format(**v).strip())

    config = combine(config, {
        v["M_MODULE_SHORT"]: {
            "config": to_literal_scalar(stdout),
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
    v["module_dir"] = get_path(str(v["shared_dir"] / v["M_MODULE_SHORT"]))
    v["config_file"] = get_path(str(v["module_dir"] / v["M_CONFIG_NAME"]))
    v["backup_file"] = get_path(str(v["module_dir"] / (v["M_CONFIG_NAME"] + ".backup")))
    v["state_file"] = get_path(str(v["shared_dir"] / v["M_STATE_FILE_NAME"]))

    epiphany_cluster = _process_epiphany_cluster(v)

    virtual_machines, epiphany_cluster = _process_virtual_machines(v, epiphany_cluster)

    components = _process_components(v, epiphany_cluster)

    applications = _process_applications(v)

    _output_data(v, [epiphany_cluster] + virtual_machines
                                       + components
                                       + [applications])
    _update_state_file(v)
