ROOT_DIR := $(patsubst %/,%,$(dir $(abspath $(firstword $(MAKEFILE_LIST)))))

AZEPI := epiphanyplatform/azepi:0.0.1

VMS_RSA_FILENAME := vms_rsa

define RUN_COMMAND
docker run --rm \
    -v $(ROOT_DIR)/shared/:/shared/ \
	-t $(AZEPI) \
	$(1)
endef

export

.PHONY: all

all: metadata init

.PHONY: metadata init plan apply plan-destroy destroy

metadata: setup
	@$(call RUN_COMMAND,$@)

init: setup
	@$(call RUN_COMMAND,$@) \
		VMS_RSA_FILENAME=$(VMS_RSA_FILENAME)

plan: setup
	@$(call RUN_COMMAND,$@)

apply: setup
	@$(call RUN_COMMAND,$@)

plan-destroy: setup
	@$(call RUN_COMMAND,$@)

destroy: setup
	@$(call RUN_COMMAND,$@)

.PHONY: clean setup

clean:
	@rm -rf $(ROOT_DIR)/shared/

setup: $(ROOT_DIR)/shared/$(VMS_RSA_FILENAME)

$(ROOT_DIR)/shared/$(VMS_RSA_FILENAME):
	@install -d $(dir $@)
	@ssh-keygen -t rsa -b 4096 -f $@ -N '' 2>&1 >/dev/null
