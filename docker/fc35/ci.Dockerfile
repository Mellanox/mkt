FROM harbor.mellanox.com/mkt/build:fc35

COPY --from=local_mkt/support_sparse:fc35 /root/rpmbuild/RPMS/x86_64/*.rpm /opt/rpms/
COPY --from=local_mkt/support_smatch:fc35 /root/rpmbuild/RPMS/x86_64/*.rpm /opt/rpms/

RUN \
    echo Israel/Jerusalem > /etc/timezone && \
    echo mellanox.com > /etc/mailname && \
    dnf install -y \
    'perl(Term::ANSIColor)' \
    'perl(Encode)' \
    'perl(DBI)' \
    'perl(Try::Tiny)' \
    'perl(bigint)' \
    python-ply \
    python-GitPython \
    clang \
    codespell \
    && dnf clean dbcache packages

RUN rpm -U /opt/rpms/*.rpm
