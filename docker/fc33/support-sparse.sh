#!/bin/bash
# ---
# git_url: https://git.kernel.org/pub/scm/devel/sparse/sparse.git
# git_commit: 49c98aa3ed1b315ed2f4fbe44271ecd5bdd9cbc7

cat <<EOF > sparse.spec
Name: sparse
Version: 0.6.0
Release: 2%{?dist}
Summary:    A semantic parser of source files
Group:      Development/Tools
License:    MIT
URL:        https://sparse.wiki.kernel.org

%description
Sparse is a semantic parser of source files: it's neither a compiler
(although it could be used as a front-end for one) nor is it a
preprocessor (although it contains as a part of it a preprocessing
phase).

It is meant to be a small - and simple - library.  Scanty and meager,
and partly because of that easy to use.  It has one mission in life:
create a semantic parse tree for some arbitrary user for further
analysis.  It's not a tokenizer, nor is it some generic context-free
parser.  In fact, context (semantics) is what it's all about - figuring
out not just what the grouping of tokens are, but what the _types_ are
that the grouping implies.

Sparse is primarily used in the development and debugging of the Linux kernel.

%prep
%setup -q

%define make_destdir \
	make DESTDIR="%{buildroot}" PREFIX="%{_prefix}" \\\
        BINDIR="%{_bindir}" LIBDIR="%{_libdir}" \\\
        INCLUDEDIR="%{_includedir}" PKGCONFIGDIR="%{_libdir}/pkgconfig" \\\
%{nil}

%build
%make_destdir %{?_smp_mflags} CFLAGS="%{optflags}"

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_libdir}
%make_destdir install

%clean
rm -rf %{buildroot}
make clean

%files
%doc LICENSE README FAQ
%{_bindir}/semind
%{_bindir}/sparse
%{_bindir}/sparse-llvm
%{_bindir}/sparsec
%{_bindir}/cgcc
%{_bindir}/c2xml
%{_mandir}/man1/*

EOF

rpmbuild --build-in-place -bb sparse.spec
