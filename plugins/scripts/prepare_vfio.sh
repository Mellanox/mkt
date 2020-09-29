#!/bin/bash -x

modprobe vfio-pci

pci_id=`lspci | grep Mellanox | head -n2 | tail -n1 | awk '{print $1}'`
vendor_id=`lspci -n -s $pci_id | awk '{ print $3 }' | awk -F ":" '{print  $1 }'`
device_id=`lspci -n -s $pci_id | awk '{ print $3 }' | awk -F ":" '{print  $2 }'`
echo 0000:$pci_id > /sys/bus/pci/devices/0000:$pci_id/driver/unbind
echo $vendor_id $device_id > /sys/bus/pci/drivers/vfio-pci/new_id
echo "$pci_id" > /tmp/vfio.id