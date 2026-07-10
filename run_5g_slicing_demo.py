#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from comnetsemu.cli import CLI, spawnXtermDocker
from comnetsemu.net import Containernet, VNFManager
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from mininet.node import Controller

from python_modules.Open5GS   import Open5GS

import json, time
import copy

from option1_latency_test import option1_menu
from option2_isolation_test import option2_menu
from option3_qos_ambr_policing import option3_menu


if __name__ == "__main__":

    setLogLevel("info")

    prj_folder="/home/comnetsemu/project_NET/comnetsemu_5Gnet"    # TO BE MODIFIED!
    mongodb_folder="/home/comnetsemu/mongodbdata"
    path_subscriber_json="/python_modules/subscriber_profile.json"

    env = dict()

    net = Containernet(controller=Controller, link=TCLink)

    info("*** Adding Host for open5gs CP\n")
    cp = net.addDockerHost(
        "cp",
        dimage="my5gc_v2-4-4",
        ip="192.168.0.111/24",
        # dcmd="",
        dcmd="bash /open5gs/install/etc/open5gs/5gc_cp_init.sh",
        docker_args={
            "ports" : { "3000/tcp": 3000 },
            "volumes": {
                prj_folder + "/log": {
                    "bind": "/open5gs/install/var/log/open5gs",
                    "mode": "rw",
                },
                mongodb_folder: {
                    "bind": "/var/lib/mongodb",
                    "mode": "rw",
                },
                prj_folder + "/open5gs/config": {
                    "bind": "/open5gs/install/etc/open5gs",
                    "mode": "rw",
                },
                "/etc/timezone": {
                    "bind": "/etc/timezone",
                    "mode": "ro",
                },
                "/etc/localtime": {
                    "bind": "/etc/localtime",
                    "mode": "ro",
                },
            },
        },
    )


    info("*** Adding Host for open5gs UPF\n")
    env["COMPONENT_NAME"]="upf_cld"
    upf_cld = net.addDockerHost(
        "upf_cld",
        dimage="my5gc_v2-4-4",
        ip="192.168.0.112/24",
        dcmd="bash /open5gs/install/etc/open5gs/temp/5gc_up_init.sh",
        docker_args={
            "environment": {"COMPONENT_NAME": "upf_cld"},
            "volumes": {
                prj_folder + "/log": {
                    "bind": "/open5gs/install/var/log/open5gs",
                    "mode": "rw",
                },
                prj_folder + "/open5gs/config": {
                    "bind": "/open5gs/install/etc/open5gs/temp",
                    "mode": "rw",
                },
                "/etc/timezone": {
                    "bind": "/etc/timezone",
                    "mode": "ro",
                },
                "/etc/localtime": {
                    "bind": "/etc/localtime",
                    "mode": "ro",
                },
            },
            "cap_add": ["NET_ADMIN"],
            "sysctls": {"net.ipv4.ip_forward": 1},
            "devices": "/dev/net/tun:/dev/net/tun:rwm"
        },
    )

    info("*** Adding Twin Cloud UPF for IoT/QoS Testing\n")
    upf_iot = net.addDockerHost(
        "upf_iot",
        dimage="my5gc_v2-4-4",
        ip="192.168.0.114/24",
        dcmd="bash /open5gs/install/etc/open5gs/temp/5gc_up_init.sh",
        docker_args={
            "environment": {"COMPONENT_NAME": "upf_iot"},
            "volumes": {
                prj_folder + "/log": {
                    "bind": "/open5gs/install/var/log/open5gs",
                    "mode": "rw",
                },
                prj_folder + "/open5gs/config": {
                    "bind": "/open5gs/install/etc/open5gs/temp",
                    "mode": "rw",
                },
                "/etc/timezone": {
                    "bind": "/etc/timezone",
                    "mode": "ro",
                },
                "/etc/localtime": {
                    "bind": "/etc/localtime",
                    "mode": "ro",
                },
            },
            "cap_add": ["NET_ADMIN"],
            "sysctls": {"net.ipv4.ip_forward": 1},
            "devices": "/dev/net/tun:/dev/net/tun:rwm"
        },
    )


    info("*** Adding Host for open5gs UPF MEC\n")
    env["COMPONENT_NAME"]="upf_mec"
    upf_mec = net.addDockerHost(
        "upf_mec",
        dimage="my5gc_v2-4-4",
        ip="192.168.0.113/24",
        dcmd="bash /open5gs/install/etc/open5gs/temp/5gc_up_init.sh",
        docker_args={
            "environment": {"COMPONENT_NAME": "upf_mec"},
            "volumes": {
                prj_folder + "/log": {
                    "bind": "/open5gs/install/var/log/open5gs",
                    "mode": "rw",
                },
                prj_folder + "/open5gs/config": {
                    "bind": "/open5gs/install/etc/open5gs/temp",
                    "mode": "rw",
                },
                "/etc/timezone": {
                    "bind": "/etc/timezone",
                    "mode": "ro",
                },
                "/etc/localtime": {
                    "bind": "/etc/localtime",
                    "mode": "ro",
                },
            },
            "cap_add": ["NET_ADMIN"],
            "sysctls": {"net.ipv4.ip_forward": 1},
            "devices": "/dev/net/tun:/dev/net/tun:rwm"
        },
    )

    info("*** Adding gNB 1\n")
    env["COMPONENT_NAME"]="gnb1"
    gnb1 = net.addDockerHost(
        "gnb1",
        dimage="myueransim_v3-2-6",
        ip="192.168.0.131/24",
        #dcmd="bash -c 'sleep 20 && ./nr-gnb -c /mnt/ueransim/open5gs-gnb1.yaml > /mnt/log/gnb1.log 2>&1'",
        docker_args={
            "environment": {"COMPONENT_NAME": "gnb1"},
            "volumes": {
                prj_folder + "/ueransim/config": { "bind": "/mnt/ueransim", "mode": "rw" },
                prj_folder + "/log": { "bind": "/mnt/log", "mode": "rw" },
                "/etc/timezone": { "bind": "/etc/timezone", "mode": "ro" },
                "/etc/localtime": { "bind": "/etc/localtime", "mode": "ro" },
                "/dev": {"bind": "/dev", "mode": "rw"},
            },
            "cap_add": ["NET_ADMIN"],
            "devices": "/dev/net/tun:/dev/net/tun:rwm"
        },
    )
    info("*** Adding gNB 2\n")
    env["COMPONENT_NAME"]="gnb2"
    gnb2 = net.addDockerHost(
        "gnb2",
        dimage="myueransim_v3-2-6",
        ip="192.168.0.132/24",
        #dcmd="bash -c 'sleep 20 && ./nr-gnb -c /mnt/ueransim/open5gs-gnb2.yaml > /mnt/log/gnb2.log 2>&1'",
        docker_args={
            "environment": {"COMPONENT_NAME": "gnb2"},
            "volumes": {
                prj_folder + "/ueransim/config": {"bind": "/mnt/ueransim", "mode": "rw"},
                prj_folder + "/log": {"bind": "/mnt/log", "mode": "rw"},
                "/etc/timezone": {"bind": "/etc/timezone", "mode": "ro"},
                "/etc/localtime": {"bind": "/etc/localtime", "mode": "ro"},
                "/dev": {"bind": "/dev", "mode": "rw"},
            },
            "cap_add": ["NET_ADMIN"],
            "devices": "/dev/net/tun:/dev/net/tun:rwm"
        },
    )

    info("*** Adding 10 UEs\n")
    ue_nodes = []
    for i in range(1, 11):
        ue_name = f"ue{i}"
        ue_ip = f"192.168.0.{140 + i}/24"
        yaml_name = f"open5gs-ue{i}.yaml"

        env["COMPONENT_NAME"] = ue_name
        ue = net.addDockerHost(
            ue_name,
            dimage="myueransim_v3-2-6",
            ip=ue_ip,
            #dcmd=f"bash -c 'sleep 25 && ./nr-ue -c /mnt/ueransim/{yaml_name} > /mnt/log/{ue_name}.log 2>&1'",
            docker_args={
                "environment": env,
                "volumes": {
                    prj_folder + "/ueransim/config": {"bind": "/mnt/ueransim", "mode": "rw"},
                    prj_folder + "/log": {"bind": "/mnt/log", "mode": "rw"},
                    "/etc/timezone": {"bind": "/etc/timezone", "mode": "ro"},
                    "/etc/localtime": {"bind": "/etc/localtime", "mode": "ro"},
                    "/dev": {"bind": "/dev", "mode": "rw"},
                },
                "cap_add": ["NET_ADMIN"],
                "devices": "/dev/net/tun:/dev/net/tun:rwm"
            },
        )
        ue_nodes.append(ue)

    info("*** Add controller\n")
    net.addController("c0")

    info("*** Adding switch\n")
    s1 = net.addSwitch("s1")
    s2 = net.addSwitch("s2")
    s3 = net.addSwitch("s3")
    s4 = net.addSwitch("s4")

    info("*** Adding links\n")
    # Shaping (HTB rate limiter) is applied only on the s2-s3 bottleneck

    # Access to Edge (MEC) - Ultra Low Latency (2ms)
    net.addLink(s1, s2, delay="2ms", intfName1="s1-s2", intfName2="s2-s1")

    # Edge to Cloud - bottleneck: 50 Mbps, 40 ms, buffer approx. 1x BDP
    # BDP = 50 Mbps x 88 ms RTT is approx. 0.55 MB, so roughly 370 full-size packets
    net.addLink(s2, s3, bw=50, delay="40ms", max_queue_size=370, 
                intfName1="s2-s3", intfName2="s3-s2")

    # Edge to IoT Cloud (twin path, uncongested reference) - High Latency (40ms)
    net.addLink(s2, s4, delay="40ms", intfName1="s2-s4", intfName2="s4-s2")

    # Control Plane at the Edge tier (s2) --> fast signaling
    net.addLink(cp, s2, delay="1ms", intfName1="cp-s2", intfName2="s2-cp")

    # UPF attachments
    net.addLink(upf_cld, s3, delay="1ms", intfName1="upf-s3", intfName2="s3-upf_cld")
    net.addLink(upf_iot, s4, delay="1ms", intfName1="upf_iot-s4", intfName2="s4-upf_iot")
    net.addLink(upf_mec, s2, delay="1ms", intfName1="upf_mec-s2", intfName2="s2-upf_mec")

    # RAN attachments
    net.addLink(gnb1, s1, delay="1ms", intfName1="gnb1-s1", intfName2="s1-gnb1")
    net.addLink(gnb2, s1, delay="1ms", intfName1="gnb2-s1", intfName2="s1-gnb2")

    # UEs
    for i, ue_node in enumerate(ue_nodes):
        ue_index = i + 1
        net.addLink(ue_node, s1, delay="1ms", 
                    intfName1=f"ue{ue_index}-s1", intfName2=f"s1-ue{ue_index}")


    print("*** Open5GS: Init subscribers for 10 UEs (Slicing)")
    o5gs = Open5GS("172.17.0.2", "27017")
    o5gs.removeAllSubscribers()

    # Load your existing JSON as a base template just for the static fields like security, etc.
    with open(prj_folder + path_subscriber_json, 'r') as f:
        base_profile = json.load(f)

    # Define the configurations for our 10 UEs
    ue_configs = [
        {"imsi": "001010000000001", "sst": 1, "dnn": "internet", "bw": 100}, # UE1 eMBB
        {"imsi": "001010000000002", "sst": 1, "dnn": "internet", "bw": 100}, # UE2 eMBB
        {"imsi": "001010000000003", "sst": 2, "dnn": "mec",      "bw": 20},  # UE3 URLLC
        {"imsi": "001010000000004", "sst": 2, "dnn": "mec",      "bw": 20},  # UE4 URLLC
        {"imsi": "001010000000005", "sst": 3, "dnn": "iot",      "bw": 1},   # UE5 mMTC
        {"imsi": "001010000000006", "sst": 3, "dnn": "iot",      "bw": 1},   # UE6 mMTC
        {"imsi": "001010000000007", "sst": 1, "dnn": "internet", "bw": 100}, # UE7 eMBB
        {"imsi": "001010000000008", "sst": 1, "dnn": "internet", "bw": 100}, # UE8 eMBB
        {"imsi": "001010000000009", "sst": 2, "dnn": "mec",      "bw": 20},  # UE9 URLLC
        {"imsi": "001010000000010", "sst": 2, "dnn": "mec",      "bw": 20},  # UE10 URLLC
    ]

    # Per-slice QoS profile:
    # - eMBB : 5QI 9  (priority 90, PDB 300 ms)
    # - URLLC: 5QI 80 (low-latency, priority 68, PDB 10 ms)
    #          ARP: highest priority (2)
    # - mMTC : 5QI 9  (lowest ARP priority, delay-tolerant)
    SLICE_QOS = {
        1: {"index": 9, "arp_pl": 8, "cap": 1, "vuln": 2},   # eMBB
        2: {"index": 80, "arp_pl": 2, "cap": 2, "vuln": 1},  # URLLC
        3: {"index": 9, "arp_pl": 14, "cap": 1, "vuln": 2},  # mMTC
    }

#    for config in ue_configs:
        # Create a deep copy of the base profile so we don't overwrite it
#        profile = copy.deepcopy(base_profile)

#        profile["imsi"] = config["imsi"]

#        profile["ambr"] = {
#            "uplink": {"value": 200, "unit": 2},    # unit 2 = Mbps
#            "downlink": {"value": 200, "unit": 2},
#        }

#        profile["slice"] = [{
#            "sst": config["sst"],
#            "sd": "000001",
#            "default_indicator": True,
#            "session": [{
#                "name": config["dnn"],
#                "type": 3,
#                "pcc_rule": [],
#                "ambr": {
#                    "uplink": {"value": config["bw"], "unit": 2},
#                    "downlink": {"value": config["bw"], "unit": 2}
#                },
#                "qos": {
#                    "index": 9 if config["sst"] == 1 else (80 if config["sst"] == 2 else 5),
#                    "arp": {"priority_level": 10, "pre_emption_capability": 1, "pre_emption_vulnerability": 1}
#                }
#            }]
#        }]

#        o5gs.addSubscriber(profile)
#        print(f"Added UE with IMSI: {config['imsi']} for SST: {config['sst']} (DNN: {config['dnn']})")
    for config in ue_configs:
        profile = copy.deepcopy(base_profile)
        profile["imsi"] = config["imsi"]

        # UE-AMBR must upper-bound the session AMBR (.json at 1 Mbps)
        # Enforced by the gNB in real 5G; UERANSIM does not enforce it, OVS emulates it
        profile["ambr"] = {
            "uplink": {"value": 200, "unit": 2},
            "downlink": {"value": 200, "unit": 2},
        }

        q = SLICE_QOS[config["sst"]]
        profile["slice"] = [{
            "sst": config["sst"],
            "sd": "000001",
            "default_indicator": True,
            "session": [{
                "name": config["dnn"],
                "type": 3,
                "pcc_rule": [],
                "ambr": {
                    "uplink": {"value": config["bw"], "unit": 2},
                    "downlink": {"value": config["bw"], "unit": 2}
                },
                "qos": {
                    "index": q["index"],
                    "arp": {
                        "priority_level": q["arp_pl"],
                        "pre_emption_capability": q["cap"],
                        "pre_emption_vulnerability": q["vuln"]
                    }
                }
            }]
        }]

        o5gs.addSubscriber(profile)
        print(f"Added IMSI {config['imsi']} | SST {config['sst']} | DNN {config['dnn']} |"
              f"AMBR {config['bw']} Mbps | 5QI {q['index']} | ARP PL {q['arp_pl']}")

    info("\n*** Starting network\n")
    net.start()

    info("*** Waiting for AMF NGAP listener\n")
    while "38412" not in cp.cmd("cat /proc/net/sctp/eps"):
        time.sleep(1)

    info("*** Starting gNBs\n")
    for name, yaml in (("gnb1", "open5gs-gnb1.yaml"), ("gnb2", "open5gs-gnb2.yaml")):
        g = net.get(name)
        g.cmd(f"/UERANSIM/build/nr-gnb -c /mnt/ueransim/{yaml} > /mnt/log/{name}.log 2>&1 &")
    for name in ("gnb1", "gnb2"):
        while "successful" not in net.get(name).cmd(
                f"grep -s 'NG Setup procedure is successful' /mnt/log/{name}.log; true"):
            time.sleep(1)
    print("*** Both gNBs registered with AMF")

    info("*** Starting UEs\n")
    DNN_SUBNET = {1: "10.45.0.0/16", 2: "10.45.0.0/16", 7: "10.45.0.0/16", 8: "10.45.0.0/16",
                  3: "10.46.0.0/16", 4: "10.46.0.0/16", 9: "10.46.0.0/16", 10: "10.46.0.0/16",
                  5: "10.47.0.0/16", 6: "10.47.0.0/16"}
    for i, ue in enumerate(ue_nodes, 1):
        ue.cmd(f"/UERANSIM/build/nr-ue -c /mnt/ueransim/open5gs-ue{i}.yaml > /mnt/log/ue{i}.log 2>&1 &")
    for i, ue in enumerate(ue_nodes, 1):
        while "inet" not in ue.cmd("ip -4 addr show uesimtun0 2>/dev/null"):
            time.sleep(1)

        # route this UE's DN subnet through its PDU session
        ue.cmd(f"ip route replace {DNN_SUBNET[i]} dev uesimtun0")
        print(f"    ue{i}: PDU session up")

#    info("*** Disabling NIC offloads\n")
#    for sw_name in ("s1", "s2", "s3", "s4"):
#        sw = net.get(sw_name)
#        for intf in sw.intfList():
#            if intf.name != "lo":
#                sw.cmd(f"ethtool -K {intf.name} tso off gso off gro off")
#    for h in [cp, upf_cld, upf_mec, upf_iot, gnb1, gnb2] + ue_nodes:
#        for intf in h.intfList():
#            if intf.name != "lo":
#                h.cmd(f"ethtool -K {intf.name} tso off gso off gro off 2>/dev/null")

    info("*** Warming up tunnel paths\n")
    DN_GW = {1: "10.45.0.1", 2: "10.45.0.1", 7: "10.45.0.1", 8: "10.45.0.1",
             3: "10.46.0.1", 4: "10.46.0.1", 9: "10.46.0.1", 10: "10.46.0.1",
             5: "10.47.0.1", 6: "10.47.0.1"}
    for i, ue in enumerate(ue_nodes, 1):
        ue.cmd(f"ping -c 1 -W 1 {DN_GW[i]} > /dev/null 2>&1")

    # *** 5G Core - AMBR Policies for mMTC devices ***
    s1 = net.get('s1')
    ue5 = net.get('ue5')
    ue6 = net.get('ue6')

    s1_ue5_port = s1.connectionsTo(ue5)[0][0].name
    s1_ue6_port = s1.connectionsTo(ue6)[0][0].name

    #interface_ue5 = ue5.defaultIntf().name
    #interface_ue6 = ue6.defaultIntf().name

    s1.cmd(f"ovs-vsctl set interface {s1_ue5_port} ingress_policing_rate=5000")
    s1.cmd(f"ovs-vsctl set interface {s1_ue5_port} ingress_policing_burst=1000")

    s1.cmd(f"ovs-vsctl set interface {s1_ue6_port} ingress_policing_rate=5000")
    s1.cmd(f"ovs-vsctl set interface {s1_ue6_port} ingress_policing_burst=1000")

    #ue5.cmd(f"tc qdisc del dev {interface_ue5} root 2>/dev/null")
    #ue5.cmd(f"tc qdisc add dev {interface_ue5} root tbf rate 5mbit burst 32kbit latency 20ms")

    #ue6.cmd(f"tc qdisc del dev {interface_ue6} root 2>/dev/null")
    #ue6.cmd(f"tc qdisc add dev {interface_ue6} root tbf rate 5mbit burst 32kbit latency 20ms")

    #if not AUTOTEST_MODE:
    #    print("\n*** Network successfully started! ***\n")

    while True:
        print("\n\033[95m" + "#"*50)
        print(" 5G NETWORK SLICING: MAIN MENU")
        print("#"*50 + "\033[0m")
        print(" Option [1] : Latency Test")
        print(" Option [2] : Inter-Slice Performance Isolation Test")
        print(" Option [3] : Slice-Specific QoS and AMBR Policing Test")
        print(" Option [4] : Drop to Manual Mininet CLI")
        print(" Option [0] : Exit and Stop Network")
        print("#"*50)

        main_choice = input("Select an option (0-4): ")

        if main_choice == '1':
            option1_menu(net)
        elif main_choice == '2':
            option2_menu(net)
        elif main_choice == '3':
            option3_menu(net)
        elif main_choice == '4':
            CLI(net)
        elif main_choice == '0':
            print("\nExiting demo. Shutting down network...")
            break
        else:
            print("\nINVALID CHOICE! Try again.")

    #if not AUTOTEST_MODE:
        # spawnXtermDocker("open5gs")
        # spawnXtermDocker("gnb")
    #    CLI(net)

    net.stop()


