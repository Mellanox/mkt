FROM fedora:28
MAINTAINER Leon Romanovsky <leonro@mellanox.com>

RUN dnf install -y \
		elfutils \
		elfutils-devel \
		findutils \
		hmaccalc \
		hostname \
		make \
		xz \
		lftp \
                bc \
                bison \
                ccache \
                elfutils-libelf-devel \
                flex \
                gcc \
                git-core \
                openssl-devel \
                perl \
		libxml-devel \
		libsqlite3x-devel \
		llvm-devel \
		gcc-c++

# Overmount these directories using docker -v
RUN mkdir /ccache/ /build/ /kbuild/ /configs/

ADD do_build make.cross /kbuild/

ENV CCACHE_DIR /ccache/
ENV HOME /build/home/
ENV LANG en_US

RUN git clone git://repo.or.cz/smatch.git /kbuild/smatch
RUN git clone git://git.kernel.org/pub/scm/devel/sparse/sparse.git /kbuild/sparse

ENTRYPOINT ["/kbuild/do_build"]
