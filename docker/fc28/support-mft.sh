#!/bin/bash
# ---
# nfs_files:
#  /mswg/release/mft/mft-4.11.0/mft-4.11.0-14/linux/mft-4.11.0-14-int/RPMS/mft-int-4.11.0-14.x86_64.rpm:
#    dest: /opt/mft/
#  /mswg/release/mft/mft-4.11.0/mft-4.11.0-14/linux/mft-4.11.0-14/RPMS/mft-4.11.0-14-x86_64-rpm.tgz:
#    dest: /opt/mft/

# Maybe we should build MFT, but it looks like another nutzo thing to build...
ln /opt/mft/mft-4.11.0-14-x86_64-rpm/RPMS/mft-4.11.0-14.x86_64.rpm /opt/mft
