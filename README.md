# Mellanox Kernel Developer Toolset

This is a set of common scripts designed to help developers working with the
Linux kernel, net and RDMA user space do their jobs efficiently. This toolset
is designed to work with docker, and has few host dependencies, other than
docker being installed.

# Recommended work flow

Developers should have a hypervisor that hosts a VNC session or is otherwise
able to accommodate their daily work, generally these tools should be run
directly on the hypervisor unless otherwise noted. Developers should not work
from a VM within their hypervisor.

When working with a standard Mellanox lab server images the recommended
configuration is latest RHEL or Fedora Core, as desired.

Working sources should be FIXME

## Compiling a kernel

FIXME

## Testing a kernel and user pace in a VM

Example commands (FIXME):

```sh
$ mkt run
$ mkt run --simx device_name
$ mkt run --pci ... --simx ..
$ mkt run image_name
```

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

The command **mkt setup** will automatically prepare a Fedora Core 28
hypervisor.

## Local settings

Local preferences can be configured in the
~/.config/mellanox/mkt/*hv-hostname*.mkt file. FIXME

## Docker preperation

**mkt** uses docker images from the Mellanox private docker container registry
(harbor.mellanox.com). By default **mkt** will download required images automatically.

Images can be generated locally by running the **mkt images --no-pull** command.
This may be faster if the user has a slow network to the harbor server.
