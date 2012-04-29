#!/bin/bash

CONTROL_IP="asen.nikhef.nl"
CONTROL_PORT="8000"

CONNECT_BASE="http://${CONTROL_IP}:${CONTROL_PORT}"


function done_ipblock(){
    curl "${CONNECT_BASE}/done"
}


WORKER_ID=$(echo "`hostname`$$" | md5sum | cut -f1 -d" ")
echo "Worker ID: $WORKER_ID"

while [ 1 ]; do
    # Fetch new work
    #BLOB=$(curl "${CONNECT_BASE}/get/`hostname`/" 2>/dev/null)
    #echo $?
    #echo $BLOB

    curl "${CONNECT_BASE}/get/${WORKER_ID}/" || exit 1 | while read line ; do
        ./worker.sh $line
    done || continue

    # curl --data "$line"  "${CONNECT_BASE}/done/${WORKER_ID}/"
    sleep 2

done
