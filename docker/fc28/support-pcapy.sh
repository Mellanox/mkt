#!/bin/bash
# ---
# git_url: https://github.com/CoreSecurity/pcapy
# git_commit: 0.11.1

# Spec file from pcapy-0.11.4-3.fc29.src.rpm
cat <<EOF > pcapy.spec
Name:           pcapy
Version:        0.11.1
Release:        1%{?dist}
Summary:        A Python interface to libpcap

License:        ASL 1.1
URL:            https://www.coresecurity.com/corelabs-research/open-source-tools/pcapy

BuildRequires:  gcc-c++
BuildRequires:  python2-devel
BuildRequires:  libpcap-devel

%description
Pcapy is a Python extension module that interfaces with the libpcap
packet capture library. Pcapy enables python scripts to capture packets
on the network. Pcapy is highly effective when used in conjunction with 
a packet-handling package such as Impacket, which is a collection of 
Python classes for constructing and dissecting network packets.

%package -n python2-pcapy
Summary:        %{sum}

%{?python_provide:%python_provide python2-pcapy}

%description -n python2-pcapy
Python2 package of pcapy.
Pcapy is a Python extension module that interfaces with the libpcap
packet capture library. Pcapy enables python scripts to capture packets
on the network. Pcapy is highly effective when used in conjunction with
a packet-handling package such as Impacket, which is a collection of
Python classes for constructing and dissecting network packets.

%prep
%setup -q

%build
%py2_build

#fix encodings
sed -i 's/\r//' LICENSE
sed -i 's/\r//' README
sed -i 's/\r//' pcapy.html
iconv -f IBM850 -t UTF8 pcapy.html > pcapy.html.tmp
mv pcapy.html.tmp pcapy.html

%install
%py2_install

rm -rf %{buildroot}/usr/tests
rm -rf %{buildroot}/usr/share/doc/pcapy

%files -n python2-pcapy
%license LICENSE
%doc README pcapy.html
%{python2_sitearch}/*
EOF

rpmbuild --build-in-place -bb pcapy.spec
