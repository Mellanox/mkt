FROM harbor.mellanox.com/mkt/build:fc29

RUN \
    echo Israel/Jerusalem > /etc/timezone && \
    echo mellanox.com > /etc/mailname && \
    dnf install -y \
    'perl(Term::ANSIColor)' \
    'perl(Encode)' \
    && dnf clean dbcache packages
