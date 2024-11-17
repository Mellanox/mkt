FROM fedora:41 AS rpms

COPY --from=local_mkt/support_qemu:fc41 /root/rpmbuild/RPMS/x86_64/*.rpm /opt/rpms/
COPY --from=local_mkt/support_simx:fc41 /root/rpmbuild/RPMS/x86_64/*.rpm /opt/rpms/

RUN rm -f \
   /opt/rpms/*debug*.rpm \
   /opt/rpms/*devel*.rpm

FROM fedora:41

# Static files are done before installing to avoid prompting
ADD ./sudoers /etc/sudoers.d/local
RUN \
    echo Israel/Jerusalem > /etc/timezone && \
    echo mellanox.com > /etc/mailname && \
    dnf install -y \
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
    glibc-langpack-en \
    infiniband-diags \
    iperf \
    iperf3 \
    iproute \
    iputils \
    kmod \
    less \
    libasan \
    libibverbs-utils \
    libpcap \
    libubsan \
    lsof \
    man \
    nano \
    net-tools \
    netperf \
    openssh-server \
    opensm \
    pciutils \
    'perl(File::Basename)' \
    'perl(File::Path)' \
    'perl(Getopt::Long)' \
    'perl(strict)' \
    'perl(warnings)' \
    psmisc \
    python3 \
    python3-argcomplete \
    qemu-kvm \
    rdma-core-devel \
    rsync \
    sensible-utils \
    strace \
    sudo \
    tcpdump \
    udev \
    unzip \
    valgrind \
    wget \
    && dnf clean dbcache packages

COPY --from=rpms /opt/rpms /opt/rpms

ADD sshd_config ssh_host_rsa_key /etc/ssh/

ADD basic-setup.sh kvm-setup.sh /root/

RUN /root/basic-setup.sh && /root/kvm-setup.sh
