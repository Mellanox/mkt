# Mellanox Kernel Developer Toolset

This is a set of common scripts designed to help developers working with the
Linux kernel, net and RDMA user space do their jobs efficiently.

## Prerequisites

This toolset requires Python 3.5 or above, while **[mkt images](docs/mkt_setup.1.md)**
will handle everything else needed for successful setup and will automatically prepare
your hypervisor.

MKT heavily relies on docker to provide containerized environment and it needs modern
distribution used as a host.

Minimal host OSes are
```
Fedora 26
Ubuntu 16.04
RedHat 8
CentOS 8
```

# Documentation

**mkt** is like **git**. It incorporates multiple internal commands under the
**mkt** multiplexer. Each command has man-page style documentation that can be
viewed with **mkt cmd --help**, or online as linked below:

* **[mkt images](docs/mkt_images.1.md)**
* **[mkt run](docs/mkt_run.1.md)**
* **[mkt build](docs/mkt_build.1.md)**
* **[mkt ci](docs/mkt_ci.1.md)**

# Recommended work flow

Developers should have a hypervisor that hosts a VNC session or is otherwise
able to accommodate their daily work, generally these tools should be run
directly on the hypervisor unless otherwise noted. Developers should not work
from a VM within their hypervisor.

When working with a standard Mellanox lab server images the recommended
configuration is latest Fedora or Ubuntu, as desired. Old releases of RHEL
lack necessary kernel features and are not supported by Docker Community
Edition.

## Compiling source code

The **[mkt build](docs/mkt_build.1.md)** command provides compilation solution
to build kernel/iproute2/rdma-core with latest development tool chain.

Recommended and optimized kernel .config is located in **[configs/kconfig-kvm](configs/kconfig-kvm)**

## Testing a kernel and user pace in a VM

The **[mkt run](docs/mkt_run.1.md)** command will quickly launch a VM
containing a kernel for testing.

## Continious integration

The **[mkt ci](docs/mkt_ci.1.md)** command will perform continious integration
tests over local source code.

# Installation

The tools are currently designed to run from a source tree and **not** as root.
Clone the repository, and link the main tool into your path:

```sh
$ cd /swgwork/`whoami`
$ git clone https://github.com/Mellanox/mkt.git
$ ln -s /swgwork/`whoami`/mkt/mkt ~/bin/
```

This assumes your shell profile has configured ~/bin/ to be in your local
search path, with something like this in the .bash_profile:

```sh
PATH=$PATH:$HOME/bin
```

From time to time, **git pull** to get the latest version.

## Command line argument completion

**mkt** support command line argument completion, however it relies on python
argcomplete to be enabled in the shell. Follow the directions
https://pypi.org/project/argcomplete/#global-completion to enable this for
your shell of choice.

Several other commonly used tools make use of this, so it is recommended to
enable it globally.

## Local settings

Local preferences can be configured in the
~/.config/mellanox/mkt/*hv-hostname*.mkt file. FIXME

## Docker preparation

**mkt** uses docker images from the Mellanox private docker container registry
(harbor.mellanox.com). By default **mkt** will download required images
automatically upon first use.

Images can be generated locally by running the **[mkt
images](docs/mkt_images.1.md)** command. This may be faster if the user has a
slow network connection to the harbor server.
