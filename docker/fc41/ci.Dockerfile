FROM harbor.mellanox.com/mkt/build:fc41

# List of cross-compilers is taken from Fedora
# https://packages.fedoraproject.org/pkgs/cross-gcc/
RUN \
    echo Israel/Jerusalem > /etc/timezone && \
    echo mellanox.com > /etc/mailname && \
    dnf install -y \
    'perl(Term::ANSIColor)' \
    'perl(Encode)' \
    'perl(DBI)' \
    'perl(Try::Tiny)' \
    'perl(bigint)' \
    python-ply \
    python-GitPython \
    clang \
    codespell \
    smatch \
    sparse \
    gcc-aarch64-linux-gnu \
    gcc-alpha-linux-gnu \
    gcc-arc-linux-gnu \
    gcc-arm-linux-gnu \
    gcc-avr32-linux-gnu \
    gcc-bfin-linux-gnu \
    gcc-c6x-linux-gnu \
    gcc-frv-linux-gnu \
    gcc-h8300-linux-gnu \
    gcc-hppa-linux-gnu \
    gcc-hppa64-linux-gnu \
    gcc-ia64-linux-gnu \
    gcc-loongarch64-linux-gnu \
    gcc-m68k-linux-gnu \
    gcc-microblaze-linux-gnu \
    gcc-mips64-linux-gnu \
    gcc-mn10300-linux-gnu \
    gcc-nios2-linux-gnu \
    gcc-openrisc-linux-gnu \
    gcc-powerpc64-linux-gnu \
    gcc-powerpc64le-linux-gnu \
    gcc-ppc64-linux-gnu \
    gcc-ppc64le-linux-gnu \
    gcc-riscv64-linux-gnu \
    gcc-s390x-linux-gnu \
    gcc-sparc64-linux-gnu \
    gcc-xtensa-linux-gnu \
    && dnf clean dbcache packages
