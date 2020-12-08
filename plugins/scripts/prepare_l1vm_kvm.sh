#!/bin/bash -x

# To enable Suspend/Resume and live Migration
modprobe -r kvm_intel
modprobe kvm_intel nested=0
