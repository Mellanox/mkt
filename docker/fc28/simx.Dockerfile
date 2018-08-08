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
    && dnf clean all

ADD do-simx.sh 00*.patch /root/

RUN mkdir -p /opt/src/ && \
    cd /opt/src/ && \
    http_proxy= git clone http://webdev01.mtl.labs.mlnx:8080/git/simx.git && \
    /bin/bash /root/do-simx.sh
