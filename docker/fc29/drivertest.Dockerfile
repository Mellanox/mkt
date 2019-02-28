FROM harbor.mellanox.com/mkt/build:fc29 as rpms

COPY --from=local_mkt/support_mft:fc29 /opt/mft/*.rpm /opt/rpms/

FROM harbor.mellanox.com/mkt/kvm:fc29

RUN \
    dnf install -y \
    python2-pcapy \
    && dnf clean dbcache packages

# COPY --from=rpms /opt/rpms /opt/rpms

RUN rpm -i /opt/rpms/*.rpm --force

