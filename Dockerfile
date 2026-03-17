FROM debian:bookworm-slim

ARG SANITYCTL_VERSION=1.1.0

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates curl; \
    rm -rf /var/lib/apt/lists/*; \
    arch="$(uname -m)"; \
    case "$arch" in \
      x86_64|amd64) asset="sanityctl-linux-amd64" ;; \
      aarch64|arm64) asset="sanityctl-linux-arm64" ;; \
      *) echo "Unsupported architecture: $arch" >&2; exit 1 ;; \
    esac; \
    base="https://github.com/rafalmasiarek/py-sanityctl/releases/download/v${SANITYCTL_VERSION}"; \
    curl -fsSL -o /tmp/"$asset" "$base/$asset"; \
    curl -fsSL -o /tmp/SHA256SUMS.txt "$base/SHA256SUMS.txt"; \
    cd /tmp; \
    grep "  $asset\$" SHA256SUMS.txt | sha256sum -c -; \
    install -m 0755 "/tmp/$asset" /usr/local/bin/sanityctl; \
    rm -f "/tmp/$asset" /tmp/SHA256SUMS.txt

CMD ["sanityctl"]
