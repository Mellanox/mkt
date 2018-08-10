FROM fedora:28

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
    kmod \
    less \
    lsof \
    man \
    nano \
    net-tools \
    openssh-server \
    pciutils \
    psmisc \
    python2 \
    python-argcomplete \
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
    libibverbs-utils \
    infiniband-diags \
    iproute \
    rdma-core \
    && dnf clean dbcache packages

COPY --from=local_mkt/support_simx:fc28 /opt/simx /opt/simx

ADD sshd_config ssh_host_rsa_key /etc/ssh/

ADD basic-setup.sh kvm-setup.sh /root/

RUN /root/basic-setup.sh && /root/kvm-setup.sh
