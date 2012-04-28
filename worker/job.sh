#!/bin/bash

CONROL_IP="194.171.98.6"
CONROL_PORT="80"

CONNECT_BASE="http://${CONTROL_IP}:80"

function get_ipblock(){
    curl "${CONNECT_BASE}/get" | while read line ; do
        echo "worker.sh $line"
    done
}

function done_ipblock(){
    curl "${CONNECT_BASE}/done"
}


while [ 1 ]; do
    # Fetch new work
    curl "${CONNECT_BASE}/get" | while read line ; do
        echo "worker.sh $line"
        sleep 1
    done

done
