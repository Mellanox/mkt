#!/bin/bash

/plugins/scripts/prepare_l1vm_vfio.sh
python3 /plugins/do-nest-kvm.py --sr --sr_qemu