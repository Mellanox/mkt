#!/bin/bash

cd /sys/kernel/debug/mlx5/0000\:01\:00.0/devel/

# Create tunnel to FN1 (vhca=2)
echo 2 > hca_id 
cat CREATE_GENERAL_OBJECT
# [23877.040574] Create vHCA tunnel for vHCA id 2
# [23877.040791] Created Object ID is 1
