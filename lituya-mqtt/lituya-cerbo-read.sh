#!/bin/bash
#
# Every few seconds, ask that all values for selected topic trees are read, which causes even values that
# have not changed to be published
while true
    do
	mosquitto_pub -h venus.local -k 60 -t 'R/c0619ab56440/vebus/276/Ac/ActiveIn/L1' -m ' '
	mosquitto_pub -h venus.local -k 60 -t 'R/c0619ab56440/system/0/Dc/Battery' -m ' '
	mosquitto_pub -h venus.local -k 60 -t 'R/c0619ab56440/vebus/276/Dc' -m ' '
	sleep 1
done
