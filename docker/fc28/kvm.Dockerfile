FROM fedora:28

# Static files are done before installing to avoid prompting
ADD ./sudoers /etc/sudoers.d/local
RUN \
    echo Israel/Jerusalem > /etc/timezone && \
    echo mellanox.com > /etc/mailname && \
    dnf install -y \
    PyQt4 \
    bash-completion \
    bzip2 \
    ca-certificates \
    curl \
    dbus \
    ethtool \
    fakeroot \
    file \
    gdb \
    git-core \
    infiniband-diags \
    iproute \
    kmod \
    less \
    linuxptp \
    iperf \
    iperf3 \
    lsof \
    man \
    nano \
    net-tools \
    opensm \
    openssh-server \
    pciutils \
    psmisc \
    python-argcomplete \
    python2 \
    python2-ipaddr \
    python2-netaddr \
    python2-netifaces \
    python2-paramiko \
    python2-pathlib2 \
    python2-pyyaml \
    python3 \
    python3-argcomplete \
    qemu-kvm \
    rsync \
    sensible-utils \
    strace \
    sudo \
    tcpdump \
    traceroute \
    udev \
    unzip \
    valgrind \
    wget \
    && dnf clean dbcache packages

# FIXME: should run this via support as well
RUN pip install python-redmine==2.0.2 plumbum==1.6.7

COPY --from=local_mkt/support_simx:fc28 /opt/simx /opt/simx
COPY --from=local_mkt/support_rdma_core:fc28 /root/rpmbuild/RPMS/x86_64/*.rpm /opt/rpms/
COPY --from=local_mkt/support_pyverbs:fc28 /root/rpmbuild/RPMS/x86_64/*.rpm /opt/rpms/
COPY --from=local_mkt/support_pypacket:fc28 /root/rpmbuild/RPMS/x86_64/*.rpm /opt/rpms/
COPY --from=local_mkt/support_pcapy:fc28 /root/rpmbuild/RPMS/x86_64/*.rpm /opt/rpms/
COPY --from=local_mkt/support_netperf:fc28 /root/rpmbuild/RPMS/x86_64/*.rpm /opt/rpms/
COPY --from=local_mkt/support_ame:fc28 /root/rpmbuild/RPMS/x86_64/*.rpm /opt/rpms/
COPY --from=local_mkt/support_mft:fc28 /opt/mft/*.rpm /opt/rpms/
COPY --from=local_mkt/support_onetest:fc28 /root/rpmbuild/RPMS/x86_64/*.rpm /opt/rpms/

ADD sshd_config ssh_host_rsa_key /etc/ssh/

ADD basic-setup.sh kvm-setup.sh /root/

RUN /root/basic-setup.sh && /root/kvm-setup.sh
