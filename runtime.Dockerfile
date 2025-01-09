FROM ubuntu:jammy

ARG PREFIX=/srv/r8/monobase

ENV DEBIAN_FRONTEND=noninteractive
ENV MONOBASE_PREFIX=$PREFIX
ENV PATH=$MONOBASE_PREFIX/bin:$PATH
ENV TZ=Etc/UTC

RUN --mount=type=bind,src=.,dst=/src,ro \
    apt-get update \
    && apt-get install -y $(grep -v '^#' </src/apt-dependencies.txt) \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=bind,src=.,dst=/src,ro \
    ln -sv /usr/bin/tini /sbin/tini \
    && mkdir -p /opt/r8/monobase \
    && ls -la /src/ \
    && cp /src/src/monobase/activate.sh /src/src/monobase/exec.sh /opt/r8/monobase/

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/opt/r8/monobase/exec.sh", "bash", "-l"]
