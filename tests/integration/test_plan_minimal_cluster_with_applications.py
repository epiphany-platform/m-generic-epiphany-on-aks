import sys
import docker
import pathlib
import tempfile


DOCKER_IMAGE_NAME = "epiphanyplatform/azepi:latest"

VARIABLES = {}

STATE_FILE_MOCK = '''
kind: state
azbi:
  status: applied
  size: 2
  use_public_ip: false
  location: northeurope
  name: azbi
  address_space:
    - 10.0.0.0/16
  address_prefixes:
    - 10.0.1.0/24
  rsa_pub_path: /shared/vms_rsa.pub
  output:
    private_ips.value:
      - 10.0.1.4
      - 10.0.1.5
    public_ips.value: []
    rg_name.value: azbi-rg
    vm_names.value:
      - azbi-0
      - azbi-1
    vnet_name.value: azbi-vnet
azepi:
  status: applied
  config: |
    kind: epiphany-cluster
    title: Epiphany cluster Config
    name: azepi
    provider: any
    specification:
      name: azepi
      admin_user:
        name: operations
        key_path: /shared/vms_rsa
      cloud:
        k8s_as_cloud_service: true
      components:
        repository:
          count: 1
          machines:
            - default-azbi-1
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
          machines:
            - default-azbi-2
        load_balancer:
          count: 0
        rabbitmq:
          count: 0
    ---
    kind: infrastructure/machine
    title: "Virtual Machine Infra"
    provider: any
    name: default-azbi-1
    specification:
      ip: 10.0.1.4
      hostname: azbi-1
    ---
    kind: infrastructure/machine
    title: "Virtual Machine Infra"
    provider: any
    name: default-azbi-2
    specification:
      ip: 10.0.1.5
      hostname: azbi-2
'''

MODULE_CONFIG_MOCK = '''
kind: azepi-config
azepi:
  config: |
    kind: epiphany-cluster
    title: Epiphany cluster Config
    name: azepi
    provider: any
    specification:
      name: azepi
      admin_user:
        name: operations
        key_path: /shared/vms_rsa
      cloud:
        k8s_as_cloud_service: true
      components:
        repository:
          count: 1
          machines:
            - default-azbi-1
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
          machines:
            - default-azbi-2
        load_balancer:
          count: 0
        rabbitmq:
          count: 0
    ---
    kind: infrastructure/machine
    title: "Virtual Machine Infra"
    provider: any
    name: default-azbi-1
    specification:
      ip: 10.0.1.4
      hostname: azbi-1
    ---
    kind: infrastructure/machine
    title: "Virtual Machine Infra"
    provider: any
    name: default-azbi-2
    specification:
      ip: 10.0.1.86
      hostname: azbi-2
'''

EXPECTED_OUTPUT = b'''
@@ -50 +50 @@
-    ip: 10.0.1.5
+    ip: 10.0.1.86
'''


def test_plan_minimal_cluster_with_applications():
    """Test plan method for mininal cluster config with postgresql and applications enabled."""

    client = docker.from_env()

    with tempfile.TemporaryDirectory() as shared_dir_name:
        shared_dir = pathlib.Path(shared_dir_name)

        with (shared_dir / "state.yml").open("w") as stream:
            stream.write(STATE_FILE_MOCK)

        module_dir = shared_dir / "azepi"
        module_dir.mkdir(parents=True, exist_ok=True)

        with (module_dir / "azepi-config.yml").open("w") as stream:
            stream.write(MODULE_CONFIG_MOCK)

        container = client.containers.run(
            DOCKER_IMAGE_NAME,
            auto_remove=False,
            detach=True,
            volumes={
                str(shared_dir.resolve()): {"bind": "/shared/", "mode": "rw"},
            },
            command=[
                "plan",
                # Create KEY=VALUE style parameters (makefile-like)
                *map("=".join, VARIABLES.items()),
            ],
        )

        try:
            container.wait()
            stdout = container.logs(stdout=True, stderr=False)
            stderr = container.logs(stdout=False, stderr=True)
        finally:
            container.remove(force=True)

        print(stderr, file=sys.stderr)

    assert stdout.strip() == EXPECTED_OUTPUT.strip()
