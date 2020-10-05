ROOT_DIR := $(patsubst %/,%,$(dir $(abspath $(firstword $(MAKEFILE_LIST)))))
CACHE_DIR := $(ROOT_DIR)/.cache

VERSION ?= 0.0.1
USER := epiphanyplatform
IMAGE := azepi

IMAGE_NAME_NO_VERSION := $(USER)/$(IMAGE)
IMAGE_NAME            := $(IMAGE_NAME_NO_VERSION):$(VERSION)

export

#used for correctly setting shared folder permissions
HOST_UID := $(shell id -u)
HOST_GID := $(shell id -g)

.PHONY: all

all: build

.PHONY: epicli build

epicli: guard-IMAGE
	@install -d $(CACHE_DIR)/epiphany/
	cd $(CACHE_DIR)/epiphany/ && git clone --depth=1 --branch=develop https://github.com/epiphany-platform/epiphany.git . || ( \
		git fetch origin develop \
		&& git checkout develop \
		&& git clean -df \
		&& git reset --hard origin/develop \
	)
	cd $(CACHE_DIR)/epiphany/ && docker build -t epicli-$(IMAGE)-develop .

build: guard-VERSION guard-IMAGE guard-USER epicli
	docker build \
		--build-arg ARG_BASE_IMAGE=epicli-$(IMAGE)-develop \
		--build-arg ARG_M_VERSION=$(VERSION) \
		--build-arg ARG_HOST_UID=$(HOST_UID) \
		--build-arg ARG_HOST_GID=$(HOST_GID) \
		-t $(IMAGE_NAME) \
		.
	docker tag $(IMAGE_NAME) $(IMAGE_NAME_NO_VERSION):latest

.PHONY: pipenv-lock pipenv-sync

pipenv-lock:
	pipenv lock --three --python=3.7 --dev

pipenv-sync:
	pipenv sync --three --python=3.7 --dev

.PHONY: lint format diff

lint:
	cd $(ROOT_DIR)/ && pylint_runner --rcfile pylintrc

format:
	cd $(ROOT_DIR)/ && autopep8 --in-place --recursive ./resources/ ./tests/

diff:
	cd $(ROOT_DIR)/ && git diff

.PHONY: test test-unit test-integration

test: test-unit test-integration

test-unit:
	cd $(ROOT_DIR)/ && PYTHONPATH=$(ROOT_DIR)/resources pytest -vv ./tests/unit/

test-integration: build
	cd $(ROOT_DIR)/ && PYTHONPATH=$(ROOT_DIR)/resources pytest -vv ./tests/integration/

guard-%:
	@if [ "${${*}}" = "" ]; then \
		echo "Environment variable $* not set"; \
		exit 1; \
	fi
