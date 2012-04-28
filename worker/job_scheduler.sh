#!/bin/bash

JOB="job.sh"

CPU_COUNT=`cat /proc/cpuinfo | grep processor | wc -l`
#CPU_COUNT=4
JOB_COUNT=$(($CPU_COUNT*2))


for ((i=0; i<${JOB_COUNT};++)); do
    $JOB &
    CHILD_PID[$i]=$!
done

for ((i=0; i<${JOB_COUNT};++)); do
    wait ${CHILD_PID[$i]}
done
