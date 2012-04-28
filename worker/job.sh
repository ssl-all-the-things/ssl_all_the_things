#!/bin/bash

CONROL_IP="194.171.98.6"
CONROL_PORT="80"

CONNECT_BASE="http://${CONTROL_IP}:80"

function get_ipblock(){
    MY_GET=`curl "${CONNECT_BASE}/get"`
}

function done_ipblock(){
    curl "${CONNECT_BASE}/done"
}


while [ 1 ]; do
    

done
