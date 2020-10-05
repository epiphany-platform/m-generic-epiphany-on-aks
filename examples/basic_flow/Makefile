ROOT_DIR := $(patsubst %/,%,$(dir $(abspath $(firstword $(MAKEFILE_LIST)))))

M_NAME ?= mop-module-tests

AZBI := epiphanyplatform/azbi:0.0.1
AZKS := epiphanyplatform/azks:0.0.1
AZEPI := epiphanyplatform/azepi:0.0.1

VMS_RSA_FILENAME := vms_rsa

define RUN_AZBI
docker run --rm \
	-v $(ROOT_DIR)/shared/:/shared/ \
	-t $(AZBI) \
	$(1) \
	M_ARM_CLIENT_ID=$$ARM_CLIENT_ID \
	M_ARM_CLIENT_SECRET=$$ARM_CLIENT_SECRET \
	M_ARM_SUBSCRIPTION_ID=$$ARM_SUBSCRIPTION_ID \
	M_ARM_TENANT_ID=$$ARM_TENANT_ID
endef

define RUN_AZKS
docker run --rm \
	-v $(ROOT_DIR)/shared/:/shared/ \
	-t $(AZKS) \
	$(1) \
	M_ARM_CLIENT_ID=$$ARM_CLIENT_ID \
	M_ARM_CLIENT_SECRET=$$ARM_CLIENT_SECRET \
	M_ARM_SUBSCRIPTION_ID=$$ARM_SUBSCRIPTION_ID \
	M_ARM_TENANT_ID=$$ARM_TENANT_ID
endef

define RUN_AZEPI
docker run --rm \
	-v $(ROOT_DIR)/shared/:/shared/ \
	-t $(AZEPI) \
	$(1)
endef

-include ./azure.mk

export

.PHONY: all apply destroy clean

all: apply

apply: init-azbi plan-azbi apply-azbi \
       init-azks plan-azks apply-azks \
       init-azepi plan-azepi apply-azepi

destroy: plan-destroy-azks destroy-azks \
         plan-destroy-azbi destroy-azbi

clean:
	@rm -rf $(ROOT_DIR)/shared/

.PHONY: init-azbi plan-azbi apply-azbi output-azbi plan-destroy-azbi destroy-azbi

init-azbi: setup
	@$(call RUN_AZBI,init) \
		M_NAME=$(M_NAME) \
		M_VMS_COUNT=2 \
		M_PUBLIC_IPS=true

plan-azbi: setup
	@$(call RUN_AZBI,plan)

apply-azbi: setup
	@$(call RUN_AZBI,apply)

output-azbi: setup
	@$(call RUN_AZBI,output)

plan-destroy-azbi: setup
	@$(call RUN_AZBI,plan-destroy)

destroy-azbi: setup
	@$(call RUN_AZBI,destroy)

.PHONY: init-azks plan-azks apply-azks output-azks plan-destroy-azks destroy-azks

init-azks: setup
	@$(call RUN_AZKS,init) \
		M_NAME=$(M_NAME)

plan-azks: setup
	@$(call RUN_AZKS,plan)

apply-azks: setup
	@$(call RUN_AZKS,apply) \
		kubeconfig

output-azks: setup
	@$(call RUN_AZKS,output)

plan-destroy-azks: setup
	@$(call RUN_AZKS,plan-destroy)

destroy-azks: setup
	@$(call RUN_AZKS,destroy)

.PHONY: init-azepi plan-azepi apply-azepi

init-azepi: setup
	@$(call RUN_AZEPI,init) \
		VMS_RSA_FILENAME=$(VMS_RSA_FILENAME)
	@install -d $(ROOT_DIR)/shared/build/azepi/
	@cp $(ROOT_DIR)/shared/kubeconfig $(ROOT_DIR)/shared/build/azepi/

plan-azepi: setup
	@$(call RUN_AZEPI,plan)

apply-azepi: setup
	@$(call RUN_AZEPI,apply)

.PHONY: setup

setup: $(ROOT_DIR)/shared/$(VMS_RSA_FILENAME)

$(ROOT_DIR)/shared/$(VMS_RSA_FILENAME):
	@mkdir -p $(dir $@)
	@ssh-keygen -t rsa -b 4096 -f $@ -N '' 2>&1 >/dev/null
