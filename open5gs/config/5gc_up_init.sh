#!/bin/bash

if [[ -z "$COMPONENT_NAME" ]]; then
	echo "Error: COMPONENT_NAME environment variable not set"; exit 1;

elif [[ "$COMPONENT_NAME" =~ ^upf_cld$ ]]; then
    UPF_IP="192.168.0.112"; TUN_NET="10.45.0.1/16"; TUN_IP="10.45.0.1"
    cp /open5gs/install/etc/open5gs/temp/upf_cld.yaml /open5gs/install/etc/open5gs/upf.yaml

elif [[ "$COMPONENT_NAME" =~ ^upf_mec$ ]]; then
    UPF_IP="192.168.0.113"; TUN_NET="10.46.0.1/16"; TUN_IP="10.46.0.1"
    cp /open5gs/install/etc/open5gs/temp/upf_mec.yaml /open5gs/install/etc/open5gs/upf.yaml

elif [[ "$COMPONENT_NAME" =~ ^upf_iot$ ]]; then
    UPF_IP="192.168.0.114"; TUN_NET="10.47.0.1/16"; TUN_IP="10.47.0.1"
    cp /open5gs/install/etc/open5gs/temp/upf_iot.yaml /open5gs/install/etc/open5gs/upf.yaml

else
	echo "Error: Invalid component name: '$COMPONENT_NAME'"; exit 1;
fi

ip tuntap add name ogstun mode tun
ip addr add "$TUN_NET" dev ogstun
ip link set ogstun up
iptables -t nat -A POSTROUTING -s "$TUN_NET" ! -o ogstun -j MASQUERADE

# Wait fot the Mininet interface
until ip -4 addr show | grep -q "$UPF_IP"; do sleep 1; done

iperf3 -B "$TUN_IP" -s -fm &
./install/bin/open5gs-upfd
