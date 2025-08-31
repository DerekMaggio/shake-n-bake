ARG UBUNTU_VERSION

FROM ubuntu:${UBUNTU_VERSION} AS ubuntu-base

    ARG YQ_VERSION
    ARG USER_ID
    ARG GROUP_ID
    ARG GROUP_NAME
    ARG USER_NAME

    SHELL ["/bin/bash", "-o", "pipefail", "-c"]

    ENV DEBIAN_FRONTEND=noninteractive \
    TZ=UTC

    RUN userdel ubuntu \
        && groupadd --gid ${GROUP_ID} ${GROUP_NAME} \
        && useradd -m --uid ${USER_ID} --gid ${GROUP_ID} --shell /bin/bash ${USER_NAME} \
        && rm -rf /home/ubuntu

    RUN apt-get update -y \
        && apt-get install -y --no-install-recommends \
            wget \
            curl \
            gnupg \
            zip \
            ca-certificates \
            tzdata \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/* \
        && wget \
            -O /usr/bin/yq \
            --progress=dot:giga https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_amd64 \
        && chmod +x /usr/bin/yq

FROM ubuntu-base AS jdk

    ARG JAVA_VERSION
    ARG MAVEN_VERSION
    ARG USER_NAME
    ARG GROUP_NAME
    ARG USER_HOME

    SHELL ["/bin/bash", "-o", "pipefail", "-c"]

    RUN URL="https://api.azul.com/metadata/v1/zulu/packages/?java_version=${JAVA_VERSION}&os=linux&arch=x64&archive_type=tar.gz&java_package_type=jdk&javafx_bundled=true&distro_version=$(echo ${JAVA_VERSION} | cut -d'.' -f1)&release_status=ga&availability_types=CA&certifications=tck&page=1&page_size=100" \
        # Fetch the download URL for the JDK package
        && wget -qO- "$URL" \
        | yq -r ".[0].download_url" \
        # Download and extract the JDK package
        | xargs wget --progress=dot:giga -O /tmp/zulu-jdk.tar.gz \
        && mkdir -p /opt/zulu-jdk \
        && tar --strip-components=1 -C /opt/zulu-jdk -xzf /tmp/zulu-jdk.tar.gz \
        && rm -f /tmp/zulu-jdk.tar.gz \
        && find /opt/zulu-jdk \( -name "*.txt" -o -name "*.html" -o -name "demo" \) -exec rm -rf {} + \
        # Install Maven
        && wget --progress=dot:giga -O /tmp/maven.tar.gz https://archive.apache.org/dist/maven/maven-3/${MAVEN_VERSION}/binaries/apache-maven-${MAVEN_VERSION}-bin.tar.gz \
        && mkdir -p /opt/maven \
        && tar -xzf /tmp/maven.tar.gz -C /opt/maven --strip-components=1 \
        && rm /tmp/maven.tar.gz \
        # Change permissions
        && chown -R ${USER_NAME}:${GROUP_NAME} /opt/ \
        # Clean up unnecessary files
        && rm -rf \
            /opt/zulu-jdk/demo \
            /opt/zulu-jdk/sample \
            /opt/zulu-jdk/lib/src.zip \
            /opt/zulu-jdk/man

    ENV JAVA_HOME=/opt/zulu-jdk
    ENV MAVEN_HOME=/opt/maven
    ENV PATH=${JAVA_HOME}/bin:${MAVEN_HOME}/bin:${PATH}

FROM ubuntu-base AS node

    ARG NODE_VERSION
    ARG USER_NAME
    ARG GROUP_NAME
    ARG USER_HOME

    SHELL ["/bin/bash", "-o", "pipefail", "-c"]

    RUN NODE_MAJOR="$(echo "${NODE_VERSION}" | cut -d. -f1)" \
        && curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" -o nodesource_setup.sh \
        && bash nodesource_setup.sh \
        && apt-get install -y --no-install-recommends nodejs="${NODE_VERSION}-1nodesource1" \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

FROM node AS node_jdk

    ARG MAVEN_VERSION
    ARG USER_HOME
    ARG USER_NAME

    COPY \
        --from=jdk \
        --chown=huloop:huloop \
        /opt/ \
        /opt/

    ENV JAVA_HOME=/opt/zulu-jdk
    ENV MAVEN_HOME=/opt/maven
    ENV PATH=${JAVA_HOME}/bin:${MAVEN_HOME}/bin:${PATH}

FROM ubuntu-base AS jre

    ARG JAVA_VERSION
    ARG USER_NAME
    ARG GROUP_NAME
    ARG USER_HOME

    SHELL ["/bin/bash", "-o", "pipefail", "-c"]

    RUN URL="https://api.azul.com/metadata/v1/zulu/packages/?java_version=${JAVA_VERSION}&os=linux&arch=x64&archive_type=tar.gz&java_package_type=jre&javafx_bundled=true&distro_version=$(echo ${JAVA_VERSION} | cut -d'.' -f1)&release_status=ga&availability_types=CA&certifications=tck&page=1&page_size=100" \
        && wget -qO- "$URL" \
        | yq -r ".[0].download_url" \
        | xargs wget --progress=dot:giga -O /tmp/zulu-jre.tar.gz \
        && mkdir -p /opt/zulu-jre \
        && tar --strip-components=1 -C /opt/zulu-jre -xzf /tmp/zulu-jre.tar.gz \
        && rm -f /tmp/zulu-jre.tar.gz \
        && find /opt/zulu-jre \( -name "*.txt" -o -name "*.html" -o -name "demo" \) -exec rm -rf {} + \
        && chown -R ${USER_NAME}:${GROUP_NAME} /opt/zulu-jre

    ENV JRE_HOME=/opt/zulu-jre
    ENV PATH=${JRE_HOME}/bin:${PATH}

FROM jre AS tomcat

    ARG TOMCAT_VERSION
    ARG USER_NAME
    ARG GROUP_NAME
    ARG USER_HOME

    SHELL ["/bin/bash", "-o", "pipefail", "-c"]

    RUN URL="https://archive.apache.org/dist/tomcat/tomcat-$(echo "${TOMCAT_VERSION}" | cut -d'.' -f1)/v${TOMCAT_VERSION}/bin/apache-tomcat-${TOMCAT_VERSION}.tar.gz" \
        && wget --progress=dot:giga -O /tmp/tomcat.tar.gz "$URL" \
        && mkdir -p /tmp/tomcat ${USER_HOME}/tomcat \
        && tar \
            --strip-components=1 \
            -C /tmp/tomcat \
            -xzf /tmp/tomcat.tar.gz \
        && mv /tmp/tomcat/* ${USER_HOME}/tomcat/ \
        && rm /tmp/tomcat.tar.gz \
        && chown -R ${USER_NAME}:${GROUP_NAME} ${USER_HOME}/tomcat
    
    USER ${USER_NAME}
    WORKDIR ${USER_HOME}
    ENTRYPOINT ["/home/huloop/tomcat/bin/catalina.sh", "run"]

FROM ubuntu-base AS mongo

    ARG MONGO_VERSION
    ARG USER_NAME
    ARG GROUP_NAME
    ARG USER_HOME

    RUN URL="https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-ubuntu2404-${MONGO_VERSION}.tgz" \
        && wget --progress=dot:giga -O /tmp/mongodb.tgz "$URL" \
        && mkdir -p ${USER_HOME}/mongodb \
        && tar --strip-components=1 -C ${USER_HOME}/mongodb -xf /tmp/mongodb.tgz \
        && rm /tmp/mongodb.tgz \
        && mkdir -p ${USER_HOME}/mongodb/data/db ${USER_HOME}/mongodb/logs

    COPY \
        --chown=${USER_NAME}:${GROUP_NAME} \
        mongod.conf \
        ${USER_HOME}/mongodb/mongod.conf

    RUN chown -R ${USER_NAME}:${GROUP_NAME} ${USER_HOME}

    USER ${USER_NAME}
    WORKDIR ${USER_HOME}
    ENTRYPOINT ["/home/huloop/mongodb/bin/mongod", "--config", "/home/huloop/mongodb/mongod.conf"]