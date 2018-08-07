FROM lab/kvm:fc28

RUN dnf makecache # 2018.06.27
RUN dnf install -y \
    flex \
    gcc \
    gcc-c++ \
    automake \
    bison \
    git-core \
    net-tools \
    PyQt4 \
    python-devel \
    python-paramiko  \
    python-pip \
    python-setuptools \
    python2 \
    python2-Cython \
    ethtool \
    iproute \
    python-argcomplete \
    python3 \
    python3-argcomplete \
    libpcap-devel \
    && dnf clean all

ADD rdma-core/*.rpm /tmp/rdma-core/
RUN dnf install -y /tmp/rdma-core/*.rpm

RUN pip install \
    --find-links http://10.7.17.35/python_packages/onetest/stable/ \
    --process-dependency-links \
    --trusted-host 10.7.17.35 \
    --no-binary :all: onetest
