---
date: 2018-6-1
footer: MKT
header: "Mellanox Kernel Tools"
layout: page
license: 'SPDX: Linux-OpenIB'
section: 1
title: mkt ci
---

# NAME

```sh
mkt ci [options] [project]
```

# DESCRIPTION

Locally run continious integration tests over source code by forking it
to temporal directory to allow seamless work on the code during CI run.

**mkt ci** provides an ability to perform in fast and efficient way self
checks. In current form, it generates reports for kernel only, but other
projects will be added in the near future.

Checkpatch, sparse and build with extra warnings (W=1) are part of this
**mkt ci**.

#OPTIONS

*project*
:	Project to build, executed with omitted proejct will try to guess the current proejct.

*---no-checkpatch*
:	Skip checkpatch check

*---rev*
:	Specify git SHA-1 to check, by default the HEAD will be checked.

*---no-sparse*
:	Don't run sparse check.

*---no-ignore-gerrit*
:	Print error in case Gerrit junk exists in patch, this option is usefull for submitters
    to external mailing lists, who are required to rmeove all internal metadata.

*---show-all*
:	Don't filter warnings/errors related to specific patch in test. This option is handy
    for everyone who wants to fix all warnings/errors.

*---no-extra-warnings*
:	Don't run W=1 check.

# MKT

Part of the **mkt(1)** suite
