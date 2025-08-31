ARG UBUNTU_BASE_IMAGE
ARG JRE_BASE_IMAGE
ARG JDK_BASE_IMAGE

FROM ${UBUNTU_BASE_IMAGE} AS artifact-download

ARG DOWNLOAD_URL

ADD "https://aka.ms/downloadazcopy-v10-linux" /tmp/azcopy.tar.gz
RUN tar -xzf /tmp/azcopy.tar.gz -C /usr/bin --strip-components=1
RUN chmod +x /usr/bin/azcopy

RUN azcopy copy "${DOWNLOAD_URL}" /home/huloop/
RUN apt-get update \
    && apt-get install unzip -y \
    && unzip -o /home/huloop/*.zip -d /huloop_artifacts


FROM ${JDK_BASE_IMAGE} AS spring-boot-builder

    ARG JAR_FILTER

    WORKDIR /home/huloop

    COPY \
        --from=artifact-download \
            /huloop_artifacts/jars/${JAR_FILTER} \
            /home/huloop/application.jar

FROM spring-boot-builder AS spring-boot-layered-builder
    
    RUN java \
        -Djarmode=tools \
        -jar /home/huloop/application.jar \
        extract \
        --layers \
        --destination /extracted

FROM ${JRE_BASE_IMAGE} AS spring-boot-runner

    WORKDIR /home/huloop
    USER huloop

    COPY \
        --from=spring-boot-builder \
        --chown=huloop:huloop \
        /home/huloop/application.jar .

    ENTRYPOINT ["java", "-jar", "application.jar"]

FROM ${JRE_BASE_IMAGE} AS spring-boot-layered-runner
    WORKDIR /home/huloop
    USER huloop

    COPY \
        --from=spring-boot-layered-builder \
        --chown=huloop:huloop \
        /extracted/dependencies ./
    COPY \
        --from=spring-boot-layered-builder \
        --chown=huloop:huloop \
        /extracted/spring-boot-loader ./
    COPY \
        --from=spring-boot-layered-builder \
        --chown=huloop:huloop \
        /extracted/snapshot-dependencies ./
    COPY \
        --from=spring-boot-layered-builder \
        --chown=huloop:huloop \
        /extracted/application ./

    ENTRYPOINT ["java", "-jar", "application.jar"]
