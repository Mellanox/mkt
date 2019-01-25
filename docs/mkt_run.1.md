---
date: 2018-6-1
footer: MKT
header: "Mellanox Kernel Tools"
layout: page
license: 'SPDX: Linux-OpenIB'
section: 1
title: mkt run
---

# NAME

```sh
mkt run [options] [[--] os configs ...]
```

# DESCRIPTION

Launch a KVM based virtual machine with an external kernel.

The VM is launched by directly invoking qemu on an internally prepared root
file-system. The terminal will be connected to the serial console of the VM,
and then switched to the hvc0 virtio console once the system fully boot. The
console is automatically logged into the VM as the user that executes **mkt
run**.

It is the caller's responsibility to provide a Linux kernel source directory
that has the proper configuration options set to boot through KVM (FIXME: see
xyz)

Once launched the VM can be exited by pressing the key sequence 'CTRL-A
x'. CTRL-C and all other special operations are delivered into the VM, not
captured by **mkt run**.

The **os** argument refers to an operating system docker image.  If the image
is not present locally it will be downloaded automatically from the Mellanox
private docker container registry server and cached. The docker image can be
recreated locally using the **mkt images** command.

**mkt run** assumes that the system has a 'br0' Linux bridge device setup that
bridges to the physical network. If one is found it connects *eth0* in the VM
to this bridge and the VM will obtain a DHCP address. If a bridge is not
available then the VM is setup to use qemu 'hostfwd' networking that gives NAT
access to the public network and port fowards port localhost 4444 on the host
to the VM's ssh server.

The key design philosophy for **mkt run** is performance. It can typically
boot into a shell prompt of a freshly compiled kernel in only 4-5 seconds of
time. To get this some functionalities are removed, particularly rebooting is
not possible, the file system is not persistent and the amount of installed
software is limited.

# WORKFLOW

This command is intended to support a developer workflow where changes are
being made to a Linux Kernel source tree that need to be tested, using the
following loop:

1. Edit kernel source files

2. Compile the kernel using the normal 'make -j'

3. Run **mkt run** to run the new kernel and all modules

4. Test the resulting kernel interactively using user-space programs from the
   VM

5. If necessary kill the VM using 'CTRL-A x', for instance because the kernel
   oops'd.

An abbreviated loop is also available where #3 does not reload the entire
kernel, but just re-loads the modules. This is suitable for test flows that do
not damage the running kernel. (FIXME see mkt modules-reload)

# OPTIONS

*--dir DIR_PATH*
:	Export the given host path into the VM at the same location. This is
    useful to export things like user space source trees for testing.  By
    default the current user's home directory is exported.

*--kernel DIR_PATH*
:	Specify the kernel source tree to use. If not given this default to FIXME
	in the configuration file. **mkt** will automatically extract the vmlinux
	and all module from the source tree and make them available to the VM.

# INTERNAL OPERATION

Internally this tool uses docker to create the root file-system for the
virtual machine. This file-system is unique to each execution and any changes
to it are discarded after **mkt run** returns.

The file-system is exported to the VM using a plan 9 virtio file-system, not a
block device. This has some limitations as 9pfs does not implement all typical
behaviors.

The exact configuration of the operating system is described in a Dockerfile
located under **docker/OS/kvm.Dockerfile** in the source repository, but generally:

- **systemd-networkd** and **systemd-resolved** are used to setup networking

- The system has only one account that can be logged into, the root user, with
  the usual Mellanox lab password.

- The usename in the host is created in the VM and given unrestricted sudo access.

- The ssh key for all VMS is hardwired and always the same.

- Basic RDMA kernel modules are autoloaded.

Since **mkt run** invokes qemu directly to create a new KVM it must be run in
a context that can create KVMs. Generally this requires running it on the
physical machine, not in another VM. Although nested KVM virtualization exists
it is an advanced feature that requires special setup.

## NETWORKING

When **mkt run** detects it is operating on the Mellanox lab network, and it
detects a br0 interface (which must be bridged to the lab network) it
selects a free IP from the set of addresses assigned to the hypervisor and
launches a new VM instance with this MAC connected to the bridge.

Multiple instances of **mkt run** can be run in parallel, and it automatically
avoids re-using addresses assigned to existing instances. Use **docker ps**
and **docker kill** to manage running instances of **mkt run**, particularly
if they have been backgrounded by a ssh connection drop.

## SIMX DEBUG

**mkt** runs over SimX are configured to produce /opt/simx/logs/simx-qemu.log
file directly in the docker instance created by **mkt run**. By default this
file is almost empty. In order to increase verbosity level and output more
information, you are invited to add extra logger comands obtaied from SimX
developers and put it into **set_simx_log()** function of **plugins/do-kvm.py"
file.

# MKT

Part of the **mkt(1)** suite
