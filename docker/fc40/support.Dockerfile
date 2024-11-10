FROM fedora:40

RUN dnf install -y \
    bc \
    binutils \
    bison \
    ccache \
    cmake \
    ctags \
    elfutils-devel \
    elfutils-libelf-devel \
    flex \
    gcc \
    gcc-c++ \
    git-core \
    glib2-devel \
    glibc-devel.i686 \
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
    libuuid-devel \
    libxml2-devel \
    llvm-devel \
    make \
    ncurses-devel \
    ninja-build \
    pandoc \
    patch \
    perl-generators \
    perl-podlators \
    pixman-devel \
    pkg-config \
    pkgconfig \
    python3.11 \
    python3-Cython \
    python3-devel \
    python3-docutils \
    python3-distutils-extra \
    python3-sphinx \
    rpm-build \
    spice-protocol \
    spice-server-devel \
    sqlite-devel \
    systemd \
    systemd-devel \
    systemtap-sdt-devel \
    usbredir-devel \
    uuid-devel \
    valgrind-devel \
    zlib-devel \
    ImageMagick \
    dejavu-sans-fonts \
    dejavu-sans-mono-fonts \
    dejavu-serif-fonts \
    graphviz \
    google-noto-sans-cjk-fonts \
    graphviz-gd \
    latexmk \
    librsvg2-tools \
    texlive-amscls \
    texlive-amsfonts \
    texlive-amsmath \
    texlive-anyfontsize \
    texlive-capt-of \
    texlive-cmap \
    texlive-collection-fontsrecommended \
    texlive-collection-latex \
    texlive-ctex \
    texlive-ec \
    texlive-eqparbox \
    texlive-euenc \
    texlive-fancybox \
    texlive-fancyvrb \
    texlive-float \
    texlive-fncychap \
    texlive-framed \
    texlive-luatex85 \
    texlive-mdwtools \
    texlive-multirow \
    texlive-needspace \
    texlive-oberdiek \
    texlive-parskip \
    texlive-polyglossia \
    texlive-psnfss \
    texlive-tabulary \
    texlive-threeparttable \
    texlive-titlesec \
    texlive-tools \
    texlive-ucs \
    texlive-upquote \
    texlive-wrapfig \
    texlive-xecjk \
    texlive-xetex-bin \
    python3-pyyaml \
    && dnf clean dbcache packages
