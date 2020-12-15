#!/bin/bash

cd /sys/kernel/debug/mlx5/0000\:01\:00.0/devel/

# Resume fn1
echo 0 > op_mod 
echo 1 > obj_id
cat RESUME_VHCA

# Destroy tunnel to FN1 (vhca=2)
echo 1 > obj_id 
cat DESTROY_GENERAL_OBJECT
# [23877.040574] Create vHCA tunnel for vHCA id 2
# [23877.040791] Created Object ID is 1
