#bin/bash

( first=""; while true; do if [[ -n "$first" ]]; then echo '{ "keepalive-options" : ["suppress-republish"] }'; else echo ""; fi ; first=true; sleep 30; done ) | mosquitto_pub -t 'R/c0619ab56440/keepalive' -l -h venus.local
