# vi: filetype=dockerfile
FROM ubuntu:jammy@sha256:0a9887931b0e38af2e3487ed39e29436b0535c4f3f52e57745baaf79d1898956

ARG PREFIX=/srv/r8/monobase

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV MONOBASE_PREFIX=$PREFIX
ENV PATH=$MONOBASE_PREFIX/bin:$PATH
ENV PYTHONPATH=/opt/r8
ENV TZ=Etc/UTC
ENV UV_CACHE_DIR=$PREFIX/uv/cache
ENV UV_COMPILE_BYTECODE=true
ENV UV_LINK_MODE=hardlink
ENV UV_PYTHON_INSTALL_DIR=$PREFIX/uv/python
ENV UV_PYTHON_PREFERENCE=only-managed
ENV UV_TOOL_BIN_DIR=$PREFIX/bin
ENV UV_TOOL_DIR=$PREFIX/uv/tools

RUN --mount=type=bind,src=.,dst=/src,ro \
    apt-get update \
    && apt-get install -y $(grep -v '^#' </src/apt-dependencies.txt) \
    && rm -rf /var/lib/apt/lists/*

# NOTE: replace the system trust store with only the managed CA bundle. One .crt per
# cert because update-ca-certificates ignores multi-cert files, every mozilla/ cert is
# deselected in the conf, and trust_new_crts=no keeps a later ca-certificates upgrade
# from re-enabling them. ca-certificates and openssl come from apt-dependencies.txt
# (ca-certificates depends on openssl). Keep this after the last apt install, and keep
# /usr/local/share/ca-certificates/cf: the hashed links point into it.
COPY --from=851725545228.dkr.ecr.us-east-1.amazonaws.com/ca-bundle@sha256:a47867db01298e270483173b583ac6ba67cb3e2a1e0198ce4436af5e74408aae /bundle.pem /tmp/cf-bundle.pem
RUN echo 'ca-certificates ca-certificates/trust_new_crts select no' \
    | debconf-set-selections \
    && sed -i 's|^mozilla/|!mozilla/|' /etc/ca-certificates.conf \
    && mkdir -p /usr/local/share/ca-certificates/cf \
    && awk '/BEGIN CERT/{n++} n{print > sprintf("/usr/local/share/ca-certificates/cf/cf-%03d.crt",n)}' \
        /tmp/cf-bundle.pem \
    && update-ca-certificates --fresh \
    && rm -f /tmp/cf-bundle.pem

RUN --mount=type=bind,src=.,dst=/src,ro \
    ln -sv /usr/bin/tini /sbin/tini \
    && mkdir -p /opt/r8/monobase \
    && cp -r /src/src/monobase/*.sh /src/src/monobase/*.py /src/src/monobase/requirements /opt/r8/monobase/

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/opt/r8/monobase/run.sh", "monobase.build", "--help"]
