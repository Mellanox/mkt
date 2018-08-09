# Authors:
#   Leon Romanovsky <leonro@mellanox.com>
#   Jason Gunthorpe <jgg@mellanox.com>
import os
import sys
import re
import argparse
import subprocess

def switch_to_vfio(bdf, modalias):
    """Switch the kernel driver for a PCI device to vfio-pci so it can be used
    with VFIO passthrough."""
    cur_driver = os.path.join("/sys/bus/pci/devices", bdf, "driver")
    if os.path.exists(cur_driver):
        if os.readlink(cur_driver).endswith("vfio-pci"):
            return

    if not os.path.exists("/sys/bus/pci/drivers/vfio-pci"):
        subprocess.check_call(["modprobe", "vfio-pci"])

    # There kernel does not de-dup this list and provides no wy for us to
    # see, it so, remove then add.
    with open(
            "/sys/bus/pci/drivers/vfio-pci/remove_id", "wb", buffering=0) as F:
        val = "%s %s\n" % (modalias['v'], modalias['d'])
        try:
            F.write(val.encode())
            F.flush()
        except IOError:
            # can get enodev if there is no ID in the list
            pass
    with open("/sys/bus/pci/drivers/vfio-pci/new_id", "w") as F:
        F.write("%s %s\n" % (modalias['v'], modalias['d']))

    if os.path.exists(cur_driver):
        with open(os.path.join(cur_driver, "unbind"), "w") as F:
            F.write(bdf + "\n")
    with open("/sys/bus/pci/drivers/vfio-pci/bind", "w") as F:
        F.write(bdf + "\n")

    assert os.readlink(cur_driver).endswith("vfio-pci")


def vfio_enable(args):
    """Move the given PCI BDF to the vfio driver. This is an internal command used
    automatically by kvm-run"""
    sd = "/sys/bus/pci/devices/"
    for I in args.pci:
        with open(os.path.join(sd, I, "modalias")) as F:
            modalias = F.read().strip()
        modalias = {
            a: b
            for a, b in re.findall(r"([a-z]+)([0-9A-F]+)", modalias)
        }
        switch_to_vfio(I, modalias)

parser = argparse.ArgumentParser(description="VFIO enable")
parser.add_argument('--pci', metavar="PCI_BDF", action="append",
                    default=[], help="PCI BDF to move to vfio")
args = parser.parse_args()
vfio_enable(args)
