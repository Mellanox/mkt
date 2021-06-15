FROM fedora:34 as rpms

COPY --from=local_mkt/support_rdma_core:fc34 /root/rpmbuild/RPMS/x86_64/*.rpm /opt/rpms/
COPY --from=local_mkt/support_simx:fc34 /root/rpmbuild/RPMS/x86_64/*.rpm /opt/rpms/

RUN rm -f \
   /opt/rpms/*debug*.rpm \
   /opt/rpms/*ibacm*.rpm \
   /opt/rpms/*devel*.rpm \
   /opt/rpms/*iwpmd*.rpm

FROM fedora:34

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
    infiniband-diags \
    iproute \
    iputils \
    kmod \
    less \
    libasan \
    libpcap \
    libubsan \
    lsof \
    man \
    nano \
    net-tools \
    openssh-server \
    opensm \
    pciutils \
    'perl(File::Basename)' \
    'perl(File::Path)' \
    'perl(Getopt::Long)' \
    'perl(strict)' \
    'perl(warnings)' \
    psmisc \
    python2 \
    python3 \
    python3-argcomplete \
    qemu-kvm \
    rsync \
    sensible-utils \
    strace \
    sudo \
    tcpdump \
    udev \
    unzip \
    valgrind \
    wget \
    autoconf \
    automake \
    libtool \
    g++ \
    vim \
    iperf \
    crash \
    zstd \
    && dnf clean dbcache packages

COPY --from=rpms /opt/rpms /opt/rpms

ADD sshd_config ssh_host_rsa_key /etc/ssh/

ADD basic-setup.sh kvm-setup.sh /root/

RUN /root/basic-setup.sh

RUN /root/kvm-setup.sh
