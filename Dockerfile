FROM python:3.11-alpine3.20 AS builder

WORKDIR /app

RUN apk add --no-cache \
    build-base \
    linux-headers \
    binutils \
    patchelf \
    upx

COPY pyproject.toml .
COPY README.md .
COPY src ./src

RUN python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --upgrade pip setuptools wheel && \
    pip install . pyinstaller && \
    printf 'from sanityctl.cli import main\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n' > main.py && \
    pyinstaller \
      --onefile \
      --name sanityctl \
      --paths src \
      --collect-all yaml \
      --collect-all rich_argparse \
      main.py

FROM alpine:3.20

RUN apk add --no-cache \
    libstdc++ \
    ca-certificates

COPY --from=builder /app/dist/sanityctl /usr/local/bin/sanityctl

ENTRYPOINT ["sanityctl"]
CMD ["--help"]