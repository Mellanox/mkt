FROM fedora:33 as rpms

COPY --from=local_mkt/support_rdma_core:fc33 /root/rpmbuild/RPMS/x86_64/*.rpm /opt/rpms/
COPY --from=local_mkt/support_simx:fc33 /root/rpmbuild/RPMS/x86_64/*.rpm /opt/rpms/
COPY --from=local_mkt/support_qemu:fc33 /root/rpmbuild/RPMS/x86_64/*.rpm /opt/rpms/

FROM fedora:33

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
    perftest \
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
    passwd \
    nmap-ncat \
    e2fsprogs \
    udev \
    unzip \
    valgrind \
    wget \
    bc \
    binutils \
    bison \
    ccache \
    cmake \
    ctags \
    elfutils-devel \
    elfutils-libelf-devel \
    findutils \
    flex \
    gcc \
    gcc-c++ \
    git-core \
    glib2-devel \
    hostname \
    iptables-devel \
    libaio-devel \
    linux-atm-libs-devel \
    libattr-devel \
    libcap-devel \
    libcap-ng-devel \
    libdb-devel \
    libfdt-devel \
    libmnl-devel \
    libnl3-cli \
    libnl3-devel \
    libseccomp-devel \
    libudev-devel \
    libusb-devel \
    libxml2-devel \
    llvm-devel \
    && dnf clean dbcache packages

COPY --from=rpms /opt/rpms /opt/rpms

ADD sshd_config ssh_host_rsa_key /etc/ssh/

ADD basic-setup.sh kvm-setup.sh /root/

RUN /root/basic-setup.sh
#RUN /root/basic-setup_rpm.sh
RUN /root/kvm-setup.sh

RUN ls /opt
COPY --from=local_mkt/support_simx:fc33 /opt/simx-src.tar.gz /opt/
RUN ls /opt
RUN cd /opt && tar -xzvf simx-src.tar.gz
RUN ls /opt