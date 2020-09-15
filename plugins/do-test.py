cmd = ["/opt/simx/bin/qemu-system-x86_64", '-smp', 'cores=2', '-m', '1G', '-nographic',
        '-serial', 'mon:stdio', '-cpu', 'host', '-enable-kvm', '/images/artemp/src/kernel/Debian_check_qemu/debian_wheezy_amd64_standard.qcow2']

os.execvp(cmd[0], cmd)

