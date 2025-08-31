ARG JDK_BASE_IMAGE


FROM ${JDK_BASE_IMAGE} AS keystore-builder
    ARG USER_ID
    ARG GROUP_ID
    ARG GROUP_NAME
    ARG USER_NAME

    USER ${USER_NAME}
    RUN mkdir -p /opt/output/ \
        && chown -R ${USER_ID}:${GROUP_ID} /opt/output
        
    COPY --chown=${USER_NAME}:${GROUP_NAME} --chmod=755 ./entrypoint.sh /opt/entrypoint.sh
    ENTRYPOINT ["/opt/entrypoint.sh"]