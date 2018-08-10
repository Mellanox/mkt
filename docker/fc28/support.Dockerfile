FROM fedora:28

RUN dnf install -y \
    PyQt4 \
    binutils \
    cmake \
    dracut \
    findutils \
    gcc \
    gcc-c++ \
    git-core \
    glib2-devel \
    kmod \
    libaio-devel \
    libattr-devel \
    libcap-devel \
    libfdt-devel \
    libnl3-cli \
    libnl3-devel \
    libpcap-devel \
    libseccomp-devel \
    libudev-devel \
    libusb-devel \
    make \
    ninja-build \
    pandoc \
    patch \
    perl-generators \
    pixman-devel \
    pkg-config \
    pkgconfig \
    pulseaudio \
    python \
    python2-Cython \
    python2-devel \
    python2-ipaddr \
    python2-netaddr \
    python2-netifaces \
    python2-paramiko \
    python2-pathlib2 \
    python2-pyyaml \
    rpm-build \
    spice-protocol \
    spice-server-devel \
    systemd \
    systemd-devel \
    systemtap-sdt-devel \
    usbredir-devel \
    uuid-devel \
    valgrind-devel \
    zlib-devel \
    && dnf clean dbcache packages

# FIXME: should run this via support as well
RUN pip install python-redmine==2.0.2 plumbum==1.6.7
