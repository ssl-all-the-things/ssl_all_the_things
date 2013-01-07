#!/bin/bash

for (( a=1; a<=255; a++ )); do
    if [ $a -eq 127 ] || [ $a -eq 10 ] || [ $a -eq 127 ] || [ $a -eq 224 ] || [ $a -eq 232 ] || [ $a -eq 233 ]; then
        continue
    fi

    for (( b=0; b<=255; b++ )); do
        if [ $a -eq 192 -a $b -eq 168 ] || [ $a -eq 172 -a $b -ge 16 -a $b -le 31 ]; then
            continue
        fi

        echo "insert into ipv4_dispatch (oct_a, oct_b, status) values ($a, $b, 'N');"
    done
done
