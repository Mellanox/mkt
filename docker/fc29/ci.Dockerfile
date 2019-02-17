FROM harbor.mellanox.com/mkt/build:fc29

COPY --from=local_mkt/support_sparse:fc29 /root/rpmbuild/RPMS/x86_64/*.rpm /opt/rpms/

RUN \
    echo Israel/Jerusalem > /etc/timezone && \
    echo mellanox.com > /etc/mailname && \
    dnf install -y \
    'perl(Term::ANSIColor)' \
    'perl(Encode)' \
    && dnf clean dbcache packages

RUN rpm -U /opt/rpms/*.rpm
