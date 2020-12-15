#!/bin/bash

if [ -n "$1" ]; then
    ib_send_lat -n 500000 -p 1807 -d ibp1s0f0v2 localhost
else
    ib_send_lat -p 24 -n 500000
fi