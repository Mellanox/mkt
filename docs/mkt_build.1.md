---
date: 2018-6-1
footer: MKT
header: "Mellanox Kernel Tools"
layout: page
license: 'SPDX: Linux-OpenIB'
section: 1
title: mkt build
---

# NAME

```sh
mkt build [options] [project]
```

# DESCRIPTION

Locally build source code in builder container.

The builder container is prepared to be usable for known to mkt projects, like kernel,
rdma-core and iproute2. The buidler employes smart compilation techniques to speed-up it
and to utilize to the maximum hypervisor hardware.

That container automatically senses presence of CCACHE directory configured by **ccache**
field in **general** section of **mkt** configuration file and internally configures build
process to reuse it.

The whole process is performed over source code and final result is placed at the same folder
to simulate exact look and feel like execution of "make ..."  scripts in the hyerpvisor.

# OPTIONS
*project*
:	Project to build, currently supported are kernel, rdma-core and iproute2.
    Once omitted, the builder will attempt to understand the source in current
    directory and if it is one of the supported projects, it will build it.

*---clean*
:	Clean source code from intermidiate result. Equivalent to "make clean"
    in the hypervisor.

*---run-shell*
:	Run a shell inside the container instead of invoking build script.
    This option is usefull to try special build options and to execute
    special "make" with arguments, for exmaple, "make menuconfig".

*---build-recipe*
:	Provide script for complete custom build experience.

*----with-kernel-headers*
:	Install latest kernel headers from kernel source directory, used for application
    custom builds.
# MKT

Part of the **mkt(1)** suite
