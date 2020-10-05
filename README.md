# m-classic-epiphany-on-aks

Epiphany Module: Classic Epiphany on AKS

# Prepare service principal

Have a look [here](https://www.terraform.io/docs/providers/azurerm/guides/service_principal_client_secret.html).

```shell
az login
az account list #get subscription from id field
az account set --subscription="SUBSCRIPTION_ID"
az ad sp create-for-rbac --role="Contributor" --scopes="/subscriptions/SUBSCRIPTION_ID" --name="SOME_MEANINGFUL_NAME" #get appID, password, tenant, name and displayName
```

# Build image

In main directory run:

```shell
make build
```

# Prepare local python3 environment (with pipenv)

In main directory run:

```shell
make pipenv-sync
```

# Run unit tests, integration tests or all tests

In main directory run:

```shell
make test-unit
```

```shell
make test-integration
```

```shell
make test
```

# Run formatter and linter

In main directory run:

```shell
make format lint diff
```

# Deploy the basic\_flow example

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

![](https://i.imgur.com/pgkhdkK.png)

# Destroy the basic\_flow example

In `examples/basic_flow` directory run (in order):

```shell
make plan-destroy-azks destroy-azks
```

```shell
make plan-destroy-azbi destroy-azbi
```
