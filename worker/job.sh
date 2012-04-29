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
    echo "Trying GET: $line"
    curl -v "${CONNECT_BASE}/get/${WORKER_ID}/" > ${WORK_FILE} 2>/dev/null
    RC=$?

    if [ "$RC" != "0" ]; then
        continue
    fi

    MEH=`head -n 1 ${WORK_FILE}`

    cat ${WORK_FILE} | while read line ; do
        echo "Trying: ./worker.sh $line"
        ./worker.sh $line
    done
    rm ${WORK_FILE}

    UPLOAD=0
    while [ "$UPLOAD" = "0" ]; do
        echo "Trying POST: $MEH"
        echo 'curl --data "ipblock=$MEH"  "${CONNECT_BASE}/done/${WORKER_ID}/"'
        curl --data "ipblock=$MEH"  "${CONNECT_BASE}/done/${WORKER_ID}/"
        if [ "$?" = "0" ]; then
            break
        fi
    done
done

exit 0

