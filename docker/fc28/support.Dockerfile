FROM fedora:28

RUN dnf install -y \
    findutils \
    gcc \
    git-core \
    glib2-devel \
    libaio-devel \
    libattr-devel \
    libcap-devel \
    libfdt-devel \
    libnl3-cli \
    libnl3-devel \
    libseccomp-devel \
    libusb-devel \
    make \
    patch \
    pixman-devel \
    pkg-config \
    pulseaudio \
    python \
    spice-protocol \
    spice-server-devel \
    systemtap-sdt-devel \
    usbredir-devel \
    uuid-devel \
    zlib-devel \
    && dnf clean dbcache packages
