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

    #AUTOTEST_MODE = os.environ.get("COMNETSEMU_AUTOTEST_MODE", 0)

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

    #env["COMPONENT_NAME"]="ue"
    #ue = net.addDockerHost(
    #    "ue", 
    #    dimage="myueransim_v3-2-6",
    #    ip="192.168.0.132/24",
        # dcmd="",
    #    dcmd="bash /mnt/ueransim/open5gs_ue_init.sh",
    #    docker_args={
    #        "environment": env,
    #        "volumes": {
    #            prj_folder + "/ueransim/config": {
    #                "bind": "/mnt/ueransim",
    #                "mode": "rw",
    #            },
    #            prj_folder + "/log": {
    #                "bind": "/mnt/log",
    #                "mode": "rw",
    #            },
    #            "/etc/timezone": {
    #                "bind": "/etc/timezone",
    #                "mode": "ro",
    #            },
    #            "/etc/localtime": {
    #                "bind": "/etc/localtime",
    #                "mode": "ro",
    #            },
    #            "/dev": {"bind": "/dev", "mode": "rw"},
    #        },
    #        "cap_add": ["NET_ADMIN"],
    #        "devices": "/dev/net/tun:/dev/net/tun:rwm"
    #    },
    #)

    info("*** Add controller\n")
    net.addController("c0")

    info("*** Adding switch\n")
    s1 = net.addSwitch("s1")
    s2 = net.addSwitch("s2")
    s3 = net.addSwitch("s3")
    s4 = net.addSwitch("s4")

    info("*** Adding links\n")
    # Access to Edge (MEC) - Ultra Low Latency (2ms)
    net.addLink(s1, s2, bw=1000, delay="2ms", intfName1="s1-s2", intfName2="s2-s1")

    # Edge to Cloud - High Latency (40ms), Lower Bandwidth (100Mbps bottleneck)
    net.addLink(s2, s3, bw=100, delay="40ms", intfName1="s2-s3", intfName2="s3-s2")

    # Edge to Cloud (TWIN for IoT/QoS testing) - High Latency (40ms), Standard Bandwidth
    net.addLink(s2, s4, bw=1000, delay="40ms", intfName1="s2-s4", intfName2="s4-s2")

    # Connected Control Plane to Edge tier (s2) --> faster signaling
    net.addLink(cp, s2, bw=1000, delay="1ms", intfName1="cp-s2", intfName2="s2-cp")

    # Connect Cloud UPF to Cloud switch
    net.addLink(upf_cld, s3, bw=1000, delay="1ms", intfName1="upf-s3", intfName2="s3-upf_cld")

    # Connect Cloud UPF (IoT/QoS testing) to Twin Cloud switch
    net.addLink(upf_iot, s4, bw=1000, delay="1ms", intfName1="upf_iot-s4", intfName2="s4-upf_iot")

    # Connect Edge UPF to Edge switch
    net.addLink(upf_mec, s2, bw=1000, delay="1ms", intfName1="upf_mec-s2", intfName2="s2-upf_mec")

    # Connect gNBs to access switch (s1)
    net.addLink(gnb1, s1, bw=1000, delay="1ms", intfName1="gnb1-s1", intfName2="s1-gnb1")
    net.addLink(gnb2, s1, bw=1000, delay="1ms", intfName1="gnb2-s1", intfName2="s1-gnb2")

    # Connect all 10 UEs to s1
    for i, ue_node in enumerate(ue_nodes):
        ue_index = i + 1
        net.addLink(ue_node, s1, bw=1000, delay="1ms", intfName1=f"ue{ue_index}-s1", intfName2=f"s1-ue{ue_index}")


    #print(f"*** Open5GS: Init subscriber for UE 0")
    #o5gs   = Open5GS( "172.17.0.2" ,"27017")
    #o5gs.removeAllSubscribers()
    #with open( prj_folder + "/python_modules/subscriber_profile.json" , 'r') as f:
    #    profile = json.load( f )
    #o5gs.addSubscriber(profile)

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

    for config in ue_configs:
        # Create a deep copy of the base profile so we don't overwrite it
        profile = copy.deepcopy(base_profile)

        profile["imsi"] = config["imsi"]

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
                    "index": 9 if config["sst"] == 1 else (80 if config["sst"] == 2 else 5),
                    "arp": {"priority_level": 10, "pre_emption_capability": 1, "pre_emption_vulnerability": 1}
                }
            }]
        }]

        o5gs.addSubscriber(profile)
        print(f"Added UE with IMSI: {config['imsi']} for SST: {config['sst']} (DNN: {config['dnn']})")


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

    # *** 5G Core - AMBR Policies for mMTC devices ***
    s1 = net.get('s1')
    ue5 = net.get('ue5')
    ue6 = net.get('ue6')

    s1_ue5_port = s1.connectionsTo(ue5)[0][0].name
    s1_ue6_port = s1.connectionsTo(ue6)[0][0].name

    #interface_ue5 = ue5.defaultIntf().name
    #interface_ue6 = ue6.defaultIntf().name

    s1.cmd(f"ovs-vsctl set interface {s1_ue5_port} ingress_policing_rate=5000")
    s1.cmd(f"ovs-vsctl set interface {s1_ue5_port} ingress_policing_burst=500")

    s1.cmd(f"ovs-vsctl set interface {s1_ue6_port} ingress_policing_rate=5000")
    s1.cmd(f"ovs-vsctl set interface {s1_ue6_port} ingress_policing_burst=500")

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


