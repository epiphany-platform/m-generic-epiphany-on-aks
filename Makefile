ROOT_DIR := $(patsubst %/,%,$(dir $(abspath $(firstword $(MAKEFILE_LIST)))))
CACHE_DIR := $(ROOT_DIR)/.cache

VERSION ?= 0.0.1
USER := epiphanyplatform
IMAGE := azepi

export

BASE_IMAGE ?= epiphanyplatform/epicli:0.8.0-RC1
IMAGE_NAME := $(USER)/$(IMAGE)

# Used for correctly setting user permissions
HOST_UID := $(shell id -u)
HOST_GID := $(lastword $(shell stat -f "%g" /var/run/docker.sock 2>/dev/null || stat -c "%g" /var/run/docker.sock 2>/dev/null))

define DOCKER_BUILD
docker build \
	--build-arg ARG_BASE_IMAGE=epicli:$(IMAGE) \
	--build-arg ARG_M_VERSION=$(VERSION) \
	--build-arg ARG_HOST_UID=$(HOST_UID) \
	--build-arg ARG_HOST_GID=$(HOST_GID) \
	--target $(1) \
	$(if $(2),--cache-from $(IMAGE_NAME):$(2)) \
	$(if $(3),--cache-from $(IMAGE_NAME):$(3)) \
	$(if $(4),--cache-from $(IMAGE_NAME):$(4)) \
	$(if $(5),--cache-from $(IMAGE_NAME):$(5)) \
	--tag $(IMAGE_NAME):$(1) \
	.
endef

.PHONY: all

all: build

.PHONY: epicli-pull epicli-build build

epicli-pull: guard-IMAGE
	docker pull $(BASE_IMAGE)
	docker tag $(BASE_IMAGE) epicli:$(IMAGE)

epicli-build: guard-IMAGE
	@install -d $(CACHE_DIR)/epiphany/
	cd $(CACHE_DIR)/epiphany/ && git clone --branch=develop https://github.com/epiphany-platform/epiphany.git . || ( \
		git fetch origin develop \
		&& git checkout develop \
		&& git clean -df \
		&& git reset --hard origin/develop \
	)
	cd $(CACHE_DIR)/epiphany/ && docker build -t epicli:$(IMAGE) .

build: guard-VERSION guard-IMAGE guard-USER
	$(call DOCKER_BUILD,stage0,stage0)
	$(call DOCKER_BUILD,stage1,stage0,stage1)
	$(call DOCKER_BUILD,stage2,stage0,stage1,stage2)
	$(call DOCKER_BUILD,stage3,stage0,stage1,stage2,stage3)
	docker tag $(IMAGE_NAME):stage3 $(IMAGE_NAME):$(VERSION)

.PHONY: pipenv-lock pipenv-sync

pipenv-lock:
	@cd $(ROOT_DIR)/ && pipenv lock --three --python=3.7 --dev

pipenv-sync:
	@cd $(ROOT_DIR)/ && pipenv sync --three --python=3.7 --dev

.PHONY: format

format:
	@cd $(ROOT_DIR)/ && autopep8 --in-place --recursive ./workdir/ ./resources/ ./tests/ \
	                 && git diff

.PHONY: test

test: build
	@rm -rf $(CACHE_DIR)/shared/ && install -d $(CACHE_DIR)/shared/
	@docker run --rm \
		-e CACHE_DIR \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $(CACHE_DIR)/shared/:/shared/ \
		-t $(IMAGE_NAME):stage2 \
	    pytest -vv /tests/integration/

guard-%:
	@if [ "${${*}}" = "" ]; then \
		echo "Environment variable $* not set"; \
		exit 1; \
	fi
