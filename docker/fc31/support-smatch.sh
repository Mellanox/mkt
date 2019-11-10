#!/bin/bash
# ---
# git_url: git://repo.or.cz/smatch.git
# git_commit: 773e0c191fc861c1adce9688d0f459d199da5f44
# other_files:
#   - 0001-Explicitly-use-python3-to-solve-rpmbuild-error.patch

patch -p1 < /opt/0001*.patch

cat <<EOF > smatch.spec
Name: smatch
Version: 1
Release: 1%{?dist}
Summary:    A semantic parser of source files
Group:      Development/Tools
License:    MIT
URL:        http://smatch.sourceforge.net/

%description
Smatch is a semantic parser of source files.

%build
make %{?_smp_mflags}

%install
make INSTALL_PREFIX="/opt/smatch" DESTDIR="%{buildroot}" PREFIX="/opt/smatch" install
mkdir -p %{buildroot}/opt/smatch/share/smatch/smatch_data/
cp -r /opt/src/smatch_data/db %{buildroot}/opt/smatch/share/smatch/smatch_data/

%clean
make clean

%files
/opt/smatch/share/man/man1/*
/opt/smatch/bin/*
/opt/smatch/share/smatch/*
/opt/smatch/share/smatch/smatch_data/db/*
EOF

rpmbuild --build-in-place -bb smatch.spec
