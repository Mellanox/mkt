FROM harbor.mellanox.com/mkt/build:fc29 as rpms

COPY --from=local_mkt/support_ame:fc29 /root/rpmbuild/RPMS/x86_64/*.rpm /opt/drivertest_rpms/
COPY --from=local_mkt/support_mft:fc29 /opt/mft/*.rpm /opt/drivertest_rpms/
COPY --from=local_mkt/support_drivertest:fc29 /root/rpmbuild/RPMS/x86_64/*.rpm /opt/drivertest_rpms/

FROM harbor.mellanox.com/mkt/kvm:fc29

RUN dnf install -y \
    mlocate \
    python2-devel \
    python2-ipaddr \
    python2-netaddr \
    python2-netifaces \
    python2-paramiko \
    python2-pathlib2 \
    python2-pcapy \
    python2-pymongo \
    python2-pyyaml \
    PyQt4 \
    && dnf clean dbcache packages

RUN updatedb

RUN pip install python-redmine==2.0.2 pathlib2==2.3.0

COPY --from=rpms /opt/drivertest_rpms /opt/drivertest_rpms/

RUN rpm -U /opt/drivertest_rpms/*.rpm
