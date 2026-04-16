#!/bin/bash

echo "Cleaning Docker containers..."
sudo docker rm -f $(sudo docker ps -a -q)

echo "Mininet cleanup..."
sudo mn -c

#docker stop $(docker ps -aq)

#docker container prune -f

if [ "$1" == "log" ]; then
    cd log && sudo rm *.log 
fi

echo "Deleting topology interfaces..."

ACTIVE_INTERFACES=$(ip -o link show | 
	awk -F': ' '{print $2}' |
	cut -d'@' -f1 |
	grep -E '^(s[0-9]+|gnb|ue|upf|cp)')

if [ -z "$ACTIVE_INTERFACES" ]; then
    echo "No interfaces found."
else
    for interface in $ACTIVE_INTERFACES; do
        echo " -> Deleting interface: $interface"
	sudo ip link delete "$interface" 2>/dev/null
    done

fi

echo "Cleanup completed."

#sudo ip link delete s1-ue
#sudo ip link delete s2-s3
#sudo ip link delete s2-s1
#sudo ip link delete gnb-s1
#sudo ip link delete s1-gnb
#sudo ip link delete s1-cp
#sudo ip link delete gnb-s2
#sudo ip link delete s2-gnb
#sudo ip link delete s3-cp
#sudo ip link delete s1-ue1
#sudo ip link delete s1-ue2
#sudo ip link delete s1-ue3
#sudo ip link delete s2-upf_mec
#sudo ip link delete s3-upf
#sudo ip link delete s1-uegnb
