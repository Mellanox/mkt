FROM lab/base:fc28

RUN dnf install -y \
    python \
    findutils \
    gcc \
    git-core \
    libaio-devel \
    libattr-devel \
    libcap-devel \
    libfdt-devel \
    libnl3-devel \
    libnl3-cli \
    pixman-devel \
    libseccomp-devel \
    spice-protocol \
    spice-server-devel \
    libusb-devel \
    make \
    pkg-config \
    pulseaudio \
    systemtap-sdt-devel \
    uuid-devel \
    zlib-devel \
    glib2-devel \
    usbredir-devel && \
    dnf clean all

ADD do-simx.sh /root/
ADD 00*.patch /root/

RUN mkdir -p /opt/src/ && \
    cd /opt/src/ && \
    http_proxy= git clone http://webdev01.mtl.labs.mlnx:8080/git/simx.git && \
    /bin/bash /root/do-simx.sh
