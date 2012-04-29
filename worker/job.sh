#!/bin/bash

CONTROL_IP="asen.nikhef.nl"
CONTROL_PORT="8000"

CONNECT_BASE="http://${CONTROL_IP}:${CONTROL_PORT}"


function done_ipblock(){
    curl "${CONNECT_BASE}/done"
}

MEH=

WORKER_ID=$(echo "`hostname`$$" | md5sum | cut -f1 -d" ")
echo "Worker ID: $WORKER_ID"

while [ 1 ]; do
    # Fetch new work

    WORK_FILE="/tmp/${WORKER_ID}.work"
    curl "${CONNECT_BASE}/get/${WORKER_ID}/" > ${WORK_FILE} 2>/dev/null || continue

    cat ${WORK_FILE} | while read line ; do
        ./worker.sh $line
    done

    MEH=`tail -1 ${WORK_FILE}`
    echo $MEH
    rm ${WORK_FILE}

    curl --data "ipblock=$MEH"  "${CONNECT_BASE}/done/${WORKER_ID}/"
done

exit 0

