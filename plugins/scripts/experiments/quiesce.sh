#!/bin/bash

cd /sys/kernel/debug/mlx5/0000\:01\:00.0/devel/

# Quiesce fn1
echo 0 > op_mod 
echo 1 > obj_id
cat QUIESCE_VHCA

