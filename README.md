# m-generic-epiphany-on-aks

Epiphany Module: Generic Epiphany on AKS

# Prepare service principal

Have a look [here](https://www.terraform.io/docs/providers/azurerm/guides/service_principal_client_secret.html).

```shell
az login
az account list #get subscription from id field
az account set --subscription="SUBSCRIPTION_ID"
az ad sp create-for-rbac --role="Contributor" --scopes="/subscriptions/SUBSCRIPTION_ID" --name="SOME_MEANINGFUL_NAME" #get appID, password, tenant, name and displayName
```

# Pull official epicli base image

In main directory run:

```shell
make epicli-pull
```

# Build image

In main directory run:

```shell
make build
```

# Deploy the basic\_flow example

__Please make sure that you have latest azbi and azks images in your local docker daemon.__

In `examples/basic_flow` directory run (in order):

Prepare service principal config (use previously obtained values):

```shell
cat >azure.mk <<'EOF'
ARM_CLIENT_ID ?= "appId field"
ARM_CLIENT_SECRET ?= "password field"
ARM_SUBSCRIPTION_ID ?= "id field"
ARM_TENANT_ID ?= "tenant field"
EOF
```

```shell
make init-azbi plan-azbi apply-azbi
```

```shell
make init-azks plan-azks apply-azks
```

```shell
make init-azepi plan-azepi apply-azepi
```

# Destroy the basic\_flow example

In `examples/basic_flow` directory run (in order):

```shell
make plan-destroy-azks destroy-azks
```

```shell
make plan-destroy-azbi destroy-azbi
```

# For Developers

To install required pip packages into local environment (virtualenv):
```shell
$ make pipenv-sync
```

To update Pipfile.lock with latest packages:
```shell
$ make pipenv-lock
```

To automatically re-format all the python code to PEP8:
```shell
$ make format
```

To locally build epicli image from latest commits in develop branch:
```shell
$ make epicli-build
```

To run integration tests:
```shell
$ make test
```
