FROM ubuntu:xenial
RUN /bin/echo -e "deb http://archive.ubuntu.com/ubuntu/ xenial-updates main universe\ndeb http://archive.ubuntu.com/ubuntu xenial main universe\ndeb http://security.ubuntu.com/ubuntu xenial-security main universe" > /etc/apt/sources.list

# Static files are done before installing to avoid prompting
ADD ./sudoers /etc/sudoers.d/local
RUN \
    if [ ! -z "$http_proxy" ]; then \
        echo 'Acquire::http { Proxy "'$http_proxy'"; };' > /etc/apt/apt.conf.d/01proxy ; \
    fi && \
    echo America/Edmonton > /etc/timezone && \
    echo mellanox.com > /etc/mailname

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash-completion \
    bind9-host \
    bzip2 \
    ca-certificates \
    curl \
    dbus \
    dnsutils \
    ethtool \
    fakeroot \
    file \
    gdb \
    git \
    git-core \
    ibutils \
    ibverbs-utils \
    infiniband-diags \
    iproute2 \
    iputils-ping \
    kmod \
    less \
    libibmad5 \
    libibumad3 \
    libibverbs1 \
    libipathverbs1 \
    libmlx4-1 \
    libmlx5-1 \
    libmthca1 \
    libnl-3-200 \
    libnl-route-3-200 \
    libpam-systemd \
    libprotobuf9v5 \
    librdmacm1 \
    libsctp1 \
    locales \
    lsof \
    man \
    nano \
    net-tools \
    netbase \
    nfs-common \
    openssh-server \
    pciutils \
    policykit-1 \
    psmisc \
    python-argcomplete \
    python-dnspython \
    python-networkx \
    python-paramiko \
    python-pexpect \
    python-urllib3 \
    python3 \
    python3-argcomplete \
    qemu-kvm \
    rsync \
    sensible-utils \
    ssh-client \
    strace \
    sudo \
    tcpdump \
    udev \
    unzip \
    valgrind \
    wget

#ADD *.deb /tmp/
#RUN dpkg -i /tmp/*.deb && rm /tmp/*.deb

ADD sshd_config ssh_host_rsa_key /etc/ssh/

ADD basic-setup.sh container-setup.sh kvm-setup.sh do-init.sh /root/
