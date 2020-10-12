ARG ARG_BASE_IMAGE
FROM $ARG_BASE_IMAGE as stage0

# stage1: gather common stuff

FROM stage0 as stage1

ENV M_MODULE_SHORT=azepi
ENV M_CONFIG_NAME=azepi-config.yml
ENV M_STATE_FILE_NAME=state.yml

ENV M_TEMPLATES=/usr/local/epicli/data/common/defaults
ENV M_WORKDIR=/workdir
ENV M_RESOURCES=/resources
ENV M_SHARED=/shared

ENV PYTHONPATH=$M_RESOURCES:$PYTHONPATH

USER root

ARG ARG_HOST_UID=1000
ARG ARG_HOST_GID=1000

ENV HOST_UID=$ARG_HOST_UID
ENV HOST_GID=$ARG_HOST_GID

ENTRYPOINT []

# stage2: setup python environent, then run linter and unit tests

FROM stage1 as stage2

ENV M_TESTS=/tests

RUN : UPGRADE PIP \
 && pip --no-cache-dir install --upgrade \
    pip \
 && : UPGRADE/INSTALL PIPENV \
 && pip --no-cache-dir install --upgrade \
    pipenv

WORKDIR /tmp/

COPY /Pipfile /Pipfile.lock ./

RUN : INSTALL PYTHON DEPS SYSTEM WIDE \
 && pipenv --clear install --system --deploy --dev

COPY $M_WORKDIR/ $M_WORKDIR/
COPY $M_RESOURCES/ $M_RESOURCES/
COPY $M_TESTS/ $M_TESTS/

RUN : FIX ACCESS RIGHTS \
 && chown -R $HOST_UID:$HOST_GID \
    $M_WORKDIR/ \
    $M_RESOURCES/ \
    $M_TESTS/

WORKDIR $M_WORKDIR/

COPY /pylintrc ./

USER $HOST_UID:$HOST_GID

RUN : RUN LINTER \
 && find $M_WORKDIR/ $M_RESOURCES/ $M_TESTS/ -type f -name '*.py' \
  | xargs --no-run-if-empty pylint --output-format=colorized

RUN : RUN UNIT TESTS \
 && pytest -vv $M_TESTS/unit/

USER root:$HOST_GID

# stage3: produce the final image

FROM stage1 as stage3

COPY $M_WORKDIR/ $M_WORKDIR/
COPY $M_RESOURCES/ $M_RESOURCES/

RUN : FIX ACCESS RIGHTS \
 && chown -R $HOST_UID:$HOST_GID \
    $M_WORKDIR/ \
    $M_RESOURCES/

WORKDIR $M_WORKDIR/

USER $HOST_UID:$HOST_GID

ARG ARG_M_VERSION="unknown"
ENV M_VERSION=$ARG_M_VERSION

ENTRYPOINT ["/usr/local/bin/python3", "./entrypoint.py"]
