FROM ghcr.io/astral-sh/uv:python3.12-alpine

    ARG SCRIPT_FILE

    RUN adduser -D huloop
    USER huloop
    WORKDIR /

    COPY --chown=huloop:huloop --chmod=755 ${SCRIPT_FILE} /script.py
    ENTRYPOINT ["uv", "run", "/script.py"]