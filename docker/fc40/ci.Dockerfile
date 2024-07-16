FROM harbor.mellanox.com/mkt/build:fc40

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
    && dnf clean dbcache packages
