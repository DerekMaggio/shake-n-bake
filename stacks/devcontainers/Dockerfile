
ARG UBUNTU_VERSION
ARG REGISTRY
ARG DEV_CONTAINER_SOURCE

# See docker-bake.hcl in this directory for the matrix of DEV_CONTAINER_SOURCE values.
FROM ${REGISTRY}${DEV_CONTAINER_SOURCE} AS devcontainer_base

    ARG MAVEN_VERSION
    ARG USER_HOME
    ARG USER_NAME
    ARG USER_GROUP

    SHELL ["/bin/bash", "-o", "pipefail", "-c"]

    RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache

    RUN --mount=type=cache,target=/var/cache/apt,sharing=private \
        --mount=type=cache,target=/var/lib/apt,sharing=private \
            wget -qO- https://aka.ms/InstallAzureCLIDeb | bash \
                && az extension add --name ssh \ 
            && out=$(mktemp) \
                && wget -nv -O$out https://cli.github.com/packages/githubcli-archive-keyring.gpg \
                && cat $out | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
                && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
                && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
                | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
            && apt-get update \
            && apt-get install -y \
                gh \
                sudo \
                git \
                unzip \
                build-essential \
                iputils-ping \
                jq \
                vim \
                nano \
                bash-completion \
                locales \
            && apt-get clean \
            && rm -rf /var/lib/apt/lists/*
    

    RUN echo "$USER_NAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USER_NAME \
        && chmod 0440 /etc/sudoers.d/$USER_NAME \
        && locale-gen en_US.UTF-8 \
        && update-locale LANG=en_US.UTF-8

    ENV LANG=en_US.UTF-8 \
        LANGUAGE=en_US:en \
        LC_ALL=en_US.UTF-8

    COPY \
        --chown=huloop:huloop \
        --chmod=755 \
        post_attach.sh ${USER_HOME}
    
    COPY \
        --from=docker-folder \
        --chown=${USER_NAME}:${USER_GROUP} \
        --chmod=755 \
        shake_n_bake.sh \
        /usr/bin/shake-n-bake

    USER ${USER_NAME}
    WORKDIR ${USER_HOME}

FROM devcontainer_base AS huloop-dev-tools-deps

    ARG USER_NAME
    ARG USER_GROUP
    ARG USER_HOME
    ARG TERRAFORM_VERSION
    ARG MONGO_TOOLS_VERSION
    ARG MONGOSH_VERSION

    USER root
    
    SHELL ["/bin/bash", "-o", "pipefail", "-c"]

    WORKDIR /tmp
    
    RUN \
        # Terraform
        wget \
                --progress=dot:giga \
                -O terraform.zip \
                "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip" \
            && unzip -q terraform.zip \
            && mv terraform /usr/bin \
        # Docker bash completion
        && wget \
                --progress=dot:giga \
                -O /etc/bash_completion.d/docker \
                https://raw.githubusercontent.com/docker/cli/master/contrib/completion/bash/docker \
        # MongoDB tools
        && wget \
                --progress=dot:giga \
                -O /tmp/mongodb-database-tools.tgz \
                "https://fastdl.mongodb.org/tools/db/mongodb-database-tools-ubuntu2404-x86_64-${MONGO_TOOLS_VERSION}.tgz" \
            && mkdir -p /tmp/mongodb-database-tools \
            && tar \
                --strip-components=1 \
                -xf /tmp/mongodb-database-tools.tgz \
                -C /tmp/mongodb-database-tools/ \
            && mv \
                /tmp/mongodb-database-tools/bin/* \
                /usr/bin/ \
        # MongoDB shell
        && wget \
                --progress=dot:giga \
                -O /tmp/mongosh.tgz \
                "https://downloads.mongodb.com/compass/mongosh-${MONGOSH_VERSION}-linux-x64.tgz" \
            && mkdir -p /tmp/mongosh \
            && tar \
                -xf /tmp/mongosh.tgz \
                -C /tmp/mongosh \
                --strip-components=1 \
            && mv /tmp/mongosh/bin/* /usr/bin/ \
        && rm -rf /tmp/*

    USER ${USER_NAME}
    WORKDIR ${USER_HOME}

    COPY \
        --from=huloop-dev-tools \
        --chown=${USER_NAME}:${USER_GROUP} \
        .bash_aliases \
        ${USER_HOME}/.bash_aliases

FROM devcontainer_base AS huloop-v5-deps
FROM devcontainer_base AS azure-sso-deps
FROM devcontainer_base AS workflow-ui-deps