# Mellanox Kernel Developer Toolset

This is a set of common scripts designed to help developers working with the
Linux kernel, net and RDMA user space do their jobs efficiently. This toolset
is designed to work with docker, and has few host dependencies beyond that and
Python 3.5.

# Documentation

**mkt** is like **git**. It incorporates multiple internal commands under the
**mkt** multiplexer. Each command has man-page style documentation that can be
viewed with **mkt cmd --help**, or online as linked below:

* **[mkt images](docs/mkt_images.1.md)**
* **[mkt run](docs/mkt_run.1.md)**

# Recommended work flow

Developers should have a hypervisor that hosts a VNC session or is otherwise
able to accommodate their daily work, generally these tools should be run
directly on the hypervisor unless otherwise noted. Developers should not work
from a VM within their hypervisor.

When working with a standard Mellanox lab server images the recommended
configuration is latest RHEL or Fedora Core, as desired. Old releases of RHEL
lack necessary kernel features and are not supported by Docker Community
Edition.

Working sources should be FIXME

## Compiling a kernel

FIXME

## Testing a kernel and user pace in a VM

The **[mkt run](docs/mkt_run.1.md)** command will quickly launch a VM
containing a kernel for testing.

# Installation

The tools are currently designed to run from a source tree. Clone the
repository, and link the main tool into your path:

```sh
$ cd ~
$ git clone https://github.com/Mellanox/mkt.git
$ ln -s ../mkt/mkt ~/bin/
```

This assumes your shell profile has configured ~/bin/ to be in your local
search path, with something like this in the .bashrc:

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

## Hypervisor preperation

**mkt** requires a new docker to be installed to be used. Do not use the
docker that comes with the operating system, follow the directions at
https://docs.docker.com/install/

The command **mkt setup** will automatically prepare your hypervisor.
The docker version is used in **mkt** tool works on Ubuntu 16.04 and newer
and Fedora 26 and above.

## Local settings

Local preferences can be configured in the
~/.config/mellanox/mkt/*hv-hostname*.mkt file. FIXME

## Docker preperation

**mkt** uses docker images from the Mellanox private docker container registry
(harbor.mellanox.com). By default **mkt** will download required images
automatically upon first use.

Images can be generated locally by running the **[mkt
images](docs/mkt_images.1.md)** command. This may be faster if the user has a
slow network connection to the harbor server.
