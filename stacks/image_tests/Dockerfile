ARG UBUNTU_VERSION
ARG REGISTRY
ARG TAG_UNDER_TEST
ARG IMAGE_UNDER_TEST

FROM ${REGISTRY}base/ubuntu:${UBUNTU_VERSION} AS bats

    ARG USER_NAME
    ARG USER_GROUP
    ARG USER_HOME

    USER ${USER_NAME}
    WORKDIR /opt/bats/

    RUN wget \
            --progress=dot:giga \
            -O bats.tar.gz \ 
            https://github.com/bats-core/bats-core/archive/refs/tags/v1.12.0.tar.gz \
        && tar -xf bats.tar.gz \
            --strip-components=1  \
        && rm bats.tar.gz

    WORKDIR /opt/bats/plugins/bats-file
    
    RUN wget \
            --progress=dot:giga \
            -O bats-files.tar.gz \
            https://github.com/bats-core/bats-file/archive/refs/tags/v0.4.0.tar.gz \
        && tar -xf bats-files.tar.gz \
            --strip-components=1 \
        && rm bats-files.tar.gz

    WORKDIR /opt/bats/plugins/bats-assert
    RUN wget \
            --progress=dot:giga \
            -O bats-assert.tar.gz \
            https://github.com/bats-core/bats-assert/archive/refs/tags/v2.1.0.tar.gz \
        && tar -xf bats-assert.tar.gz \
            --strip-components=1 \
        && rm bats-assert.tar.gz

FROM scratch AS bats-binaries

    COPY --from=bats /opt/bats /

# See docker-bake.hcl in this directory for the matrix of DEV_CONTAINER_SOURCE values.
FROM ${REGISTRY}${IMAGE_UNDER_TEST} AS test

    ARG USER_HOME
    ARG TEST_FILES
    ARG USER_NAME
    ARG GROUP_NAME
    ARG TERRAFORM_VERSION
    ARG MONGOSH_VERSION
    ARG MONGO_TOOLS_VERSION
    ARG JAVA_VERSION
    ARG MAVEN_VERSION
    ARG NODE_VERSION
    ARG WF_NODE_VERSION
    ARG TOMCAT_VERSION
    ARG MONGO_VERSION
    
    COPY --from=bats-binaries --chown=${USER_NAME}:${GROUP_NAME} / /opt/bats
    ENV PATH="/opt/bats/bin:${PATH}"

    WORKDIR ${USER_HOME}
    COPY ./bats/ ./bats/

    WORKDIR ${USER_HOME}/bats/
    RUN bats ${TEST_FILES} || exit 1
