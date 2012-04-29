#!/bin/bash

CONTROL_IP="asen.nikhef.nl"
CONTROL_PORT="8000"

CONNECT_BASE="http://${CONTROL_IP}:${CONTROL_PORT}"


WORKER_ID=$(echo "`hostname`$$" | md5sum | cut -f1 -d" ")
echo "Worker ID: $WORKER_ID"

while [ 1 ]; do
    # Fetch new work

    WORK_FILE="/tmp/${WORKER_ID}.work"
    curl "${CONNECT_BASE}/get/${WORKER_ID}/" > ${WORK_FILE} 2>/dev/null || continue

    cat ${WORK_FILE} | while read line ; do
        ./worker.sh $line
    done
    rm ${WORK_FILE}

    curl --data "'$line'"  "${CONNECT_BASE}/done/${WORKER_ID}/"
    sleep 2

done

exit 0


