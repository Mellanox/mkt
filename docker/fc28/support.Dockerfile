FROM fedora:28

RUN dnf install -y \
    binutils \
    cmake \
    dracut \
    findutils \
    gcc \
    git-core \
    glib2-devel \
    kmod \
    libaio-devel \
    libattr-devel \
    libcap-devel \
    libfdt-devel \
    libnl3-cli \
    libnl3-devel \
    libseccomp-devel \
    libudev-devel \
    libusb-devel \
    make \
    ninja-build \
    pandoc \
    patch \
    pixman-devel \
    pkg-config \
    pkgconfig \
    pulseaudio \
    python \
    python2-Cython \
    python2-devel \
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
