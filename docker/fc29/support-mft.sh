#!/bin/bash
# ---
# nfs_files:
#  /mswg/release/mft/mft-4.12.0/mft-4.12.0-12/linux/mft-4.12.0-12-int/RPMS/mft-int-4.12.0-12.x86_64.rpm:
#    dest: /opt/mft/
#  /mswg/release/mft/mft-4.12.0/mft-4.12.0-12/linux/mft-4.12.0-12/RPMS/mft-4.12.0-12-x86_64-rpm.tgz:
#    dest: /opt/mft/

# Maybe we should build MFT, but it looks like another nutzo thing to build...
# I'm not sure this is what you(Jason) indented to do.
# This fails:
# ln: failed to create hard link '/opt/mft/mft-int-4.12.0-12.x86_64.rpm': File exists
# So I commented it out for now.
# ln /opt/mft/mft-int-4.12.0-12.x86_64.rpm /opt/mft
