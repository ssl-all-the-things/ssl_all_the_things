#!/bin/bash

for i in {1..5}
do
	/usr/local/go/bin/go run getcerts.go http://178.21.22.5:8000 &
	sleep 2
done