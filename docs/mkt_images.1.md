---
date: 2018-6-1
footer: MKT
header: "Mellanox Kernel Tools"
layout: page
license: 'SPDX: Linux-OpenIB'
section: 1
title: mkt images
---

# NAME

```sh
mkt images [options] image_key
```

# DESCRIPTION

Locally build a docker container image for *image_key*.

Docker container images are used by **mkt** for a variety of purposes,
including **mkt run**. Most images are pre-built and pushed to the Mellanox
private registry (https://harbor.mellanox.com).

# WORKFLOW

Developers working directly on **mkt**, those wishing to customize the VM
images, or those working on machines with poor network connectivity to harbor
will need to use this command.

The command creates a single docker image for the given *image_key* tag. The
key is the same key to be used with run. This involves multiple steps, all are
sequenced internally by **mkt images**

Internally the Dockerfiles are constructed to make good use of docker layer
caching to speed up rebuilding and testing of modifications. **mkt**
developers working in this area are strongly recommended to place their
*/var/lib/docker* directory on high speed solid state storage and to setup
**apt-cacher-ng** as a local http_proxy to speed up package fetching.

# SUPPORTED IMAGE_KEY

The following values are supported for *image_key*:

*fc33*
:	Build the image to support **mkt run** with Fedora Core 33 as the VM
    operating system

# OPTIONS

*--no-pull*
:	Do not update the base docker images from the public docker
	registry. These are images like the fedora starting container image. This
	option can be used by **mkt** developers to speed up image rebuilding.

*--only*
:   Build only a single docker container image tag. This is generally only
    useful after a full build has been completed, it can be used by **mkt**
    developers revising the build scripts for a support container. Use
	**docker images** to see a list of the support container tag names.

*--push*
:	Upload newly created images to harbor.mellanox.com registry. This option
	is needed for developers who has write access to that registry and are
	responsible for creating base images for the rest.

# INTERNAL OPERATION

## SUPPORT PACKAGES

Building the KVM images require compiling some external source code (eg simx,
latest rdma-core), which is done in a dedicate support docker container, not
the main KVM image. The support container has the needed compilers/etc
required to build the all the source code and the result of the source code
builds are placed into docker images.

This allows docker layer caching to speed up building the KVM image by only
rebuilding things have have had their inputs change.

Support packages are described by a shell script with instructions to build
the OS.  The **mkt** support code fetches the source code from a GIT
repository and provides it to that shell script inside a docker container
environment. See *docker/fc35/support-simx.sh* for an example

## KVM DOCKER IMAGE

The final KVM image is produced via a single docker build which incorporates
the products from the support containers using 'COPY --from' directives.

The final end product is an image tagged with the registry name, for instance
*harbor.mellanox.com/mkt/kvm*.

When building KVM images *mkt* uses the Dockerfiles and supplementary scripts
located in **docker/OS/kvm.Dockerfile**.

## KVM IMAGE DESIGN

Prior to starting the KVM each root file-system is modified by the do-kvm.py
script. The modifications it makes are matched to the setup baked into the
image, and the two usually go hand in hand. The system is setup so that
changes to do-kvm.py do not require rebuilding the image.

In turn, the image makes assumptions about how the kernel is configured. At a
minimum the kernel must include most of the 'virtio' drivers, and all of the
systemd required configuration options. The kernel must also be configured to
boot and mount the virtio 9pfs without any modules, initrd or boot-loader. All
booting is done directly via qemu.

The rest of the image construction is related to convincing a container image
to boot as a 9pfs root file-system for a KVM. This can be a challenging task
for a new OS release.

Enabling higher levels of systemd debugging, and logging to the serial console
by modifying **do-kvm.py** (search for forward_to_console), and enabling the
systemd emergency shell (search for debug-shell.service in kvm-setup.sh) are
good starting points for doing an OS upgrade.

Once the system boots into a shell, the journal and console output can be
inspected for errors which should be corrected.

Be forewarned that systemd often requires new kernel features, refer to
https://github.com/systemd/systemd/blob/master/README for guidance.

## PUBLICATION

Upon releases of **mkt** the common set of docker images should be pushed to
the harbor registry. This requires special access permissions.

# MKT

Part of the **mkt(1)** suite
