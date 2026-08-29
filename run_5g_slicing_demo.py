#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
5G Network Slicing Demo

Topology: 2 gNBs, 10 UEs across 3 slices (eMBB / URLLC / mMTC) on a distributed
user plane (Cloud / Edge-MEC / IoT UPFs). A CLI menu drives 3 tests.

Run with: sudo ./clean.sh && sudo python3 run_5g_slicing_demo.py 
"""

import json
import time
import copy

from comnetsemu.cli import CLI
from comnetsemu.net import Containernet
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from mininet.node import Controller

from python_modules.Open5GS import Open5GS
from option1_latency_test import option1_menu
from option2_isolation_test import option2_menu
from option3_qos_ambr_policing import option3_menu

# =============================================================================
# CONFIGURATION - variables
# =============================================================================
PROJECT_FOLDER = "/home/comnetsemu/project_NET/comnetsemu_5Gnet"
MONGODB_DIR = "/home/comnetsemu/mongodbdata"
SUBSCRIBERS_JSON = PROJECT_FOLDER + "/python_modules/subscriber_profile.json"

IMAGE_OPEN5GS = "my5gc_v2-4-4"
IMAGE_UERANSIM = "myueransim_v3-2-6"
MONGO_ADDR = "172.17.0.2"
MONGO_PORT = "27017"

# Transport dimensioning on Mininet
EDGE_DELAY = "2ms"    # s1 <--> s2 access to edge
BACKHAUL_BW = 100     # Mbps, s2<-->s3 edge to cloud BOTTLENECK
BACKHAUL_DELAY = "40ms"
BACKHAUL_QLEN = 700   # packets = 1x BDP (100 Mbps x 88 ms RTT)

# mMTC RAN-side rate limit (OVS ingress policing, to emulate UE-AMBR at the gNB)
MMTC_POLICY_KBPS = 5000
MMTC_POLICY_BURST = 1000

# Per-slice subscribers:  SST 1 = eMBB (Cloud), 2 = URLLC (Edge), 3 = mMTC (IoT)
UE_CONFIGS = [
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

# Per-slice QoS
SLICE_QOS = {
        1: {"index": 9, "arp_pl": 8, "cap": 1, "vuln": 2},   # eMBB : 5QI 9  non-GBR
        2: {"index": 80, "arp_pl": 2, "cap": 2, "vuln": 1},  # URLLC: 5QI 80 low-latency
        3: {"index": 9, "arp_pl": 14, "cap": 1, "vuln": 2},  # mMTC : 5QI 9  delay-tolerant
    }

# Slice (SST) --> Data network
SLICE_DN = {
    1: ("10.45.0.1", "10.45.0.0/16"),  # eMBB --> Cloud UPF (.112)
    2: ("10.46.0.1", "10.46.0.0/16"),  # URLLC --> Edge MEC UPF (.113)
    3: ("10.47.0.1", "10.47.0.0/16"),  # mMTC --> IoT UPF (.114)
}
MENU_W = 60

# =============================================================================
# Container helpers
# =============================================================================
def add_upf(net, name, ip, component):
    """Open5GS UPF container (Cloud / Edge / IoT)"""
    return net.addDockerHost(
        name, dimage = IMAGE_OPEN5GS, ip = ip,
        dcmd = "bash /open5gs/install/etc/open5gs/temp/5gc_up_init.sh",
        docker_args = {
            "environment": {"COMPONENT_NAME": component},
            "volumes": {
                PROJECT_FOLDER + "/log": {
                    "bind": "/open5gs/install/var/log/open5gs",
                    "mode": "rw"
                },
                PROJECT_FOLDER + "/open5gs/config": {
                    "bind": "/open5gs/install/etc/open5gs/temp",
                    "mode": "rw"
                },
                "/etc/timezone": {"bind": "/etc/timezone", "mode": "ro"},
                "/etc/localtime": {"bind": "/etc/localtime", "mode": "ro"},
            },
            "cap_add": ["NET_ADMIN"],
            "sysctls": {"net.ipv4.ip_forward": 1},
            "devices": "/dev/net/tun:/dev/net/tun:rwm",
        },
    )

def add_ran(net, name, ip, extra_args=None):
    """UERANSIM container (gNB or UE)"""
    args = {
        "volumes": {
            PROJECT_FOLDER + "/ueransim/config": {"bind": "/mnt/ueransim", "mode": "rw"},
            PROJECT_FOLDER + "/log": {"bind": "/mnt/log", "mode": "rw"},
            "/etc/timezone": {"bind": "/etc/timezone", "mode": "ro"},
            "/etc/localtime": {"bind": "/etc/localtime", "mode": "ro"},
            "/dev": {"bind": "/dev", "mode": "rw"},
        },
        "cap_add": ["NET_ADMIN"],
        "devices": "/dev/net/tun:/dev/net/tun:rwm",
    }
    if extra_args:
        args.update(extra_args)
    return net.addDockerHost(name, dimage = IMAGE_UERANSIM, ip = ip, docker_args = args)

def provision_subscribers():
    """Wipe and re-create the 10 slice subscribers in Open5GS"""
    o5gs = Open5GS(MONGO_ADDR, MONGO_PORT)
    o5gs.removeAllSubscribers()
    with open(SUBSCRIBERS_JSON) as f:
        base = json.load(f)
    for cfg in UE_CONFIGS:
        q = SLICE_QOS[cfg["sst"]]
        p = copy.deepcopy(base)
        p["imsi"] = cfg["imsi"]
        p["ambr"] = {"uplink": {"value": 200, "unit": 2},
                     "downlink": {"value": 200, "unit": 2}}
        p["slice"] = [{
            "sst": cfg["sst"], "sd": "000001", "default_indicator": True,
            "session": [{
                "name": cfg["dnn"], "type": 3, "pcc_rule": [],
                "ambr": {"uplink": {"value": cfg["bw"], "unit": 2},
                         "downlink": {"value": cfg["bw"], "unit": 2}},
                "qos": {"index": q["index"],
                        "arp": {"priority_level": q["arp_pl"],
                                "pre_emption_capability": q["cap"],
                                "pre_emption_vulnerability": q["vuln"]}},
            }],
        }]
        o5gs.addSubscriber(p)
        print(f"  {cfg['imsi']} | SST {cfg['sst']} | DNN {cfg['dnn']:8} | "
              f"AMBR {cfg['bw']:>3} Mbps | 5QI {q['index']} | ARP {q['arp_pl']}")

def main_menu():
    print("\n\033[95m" + "=" * MENU_W)
    print("  5G NETWORK SLICING  -  MAIN MENU")
    print("=" * MENU_W + "\033[0m")
    print("  [1] : Latency Test           per-UE RTT through 5G tunnel")
    print("  [2] : Inter-slice isolation  eMBB congestion vs. URLLC")
    print("  [3] : QoS / AMBR policing    mMTC IoT-DDoS mitigation")
    print("  [4] : Manual Mininet CLI")
    print("  [0] : Exit and stop the network")
    print("#" * MENU_W)

# =============================================================================
# Topology build and management
# =============================================================================
if __name__ == "__main__":
    setLogLevel("info")
    net = Containernet(controller=Controller, link=TCLink)

    info("*** Adding 5G core control plane (cp)\n")
    cp = net.addDockerHost(
        "cp", dimage = IMAGE_OPEN5GS, ip = "192.168.0.111/24",
        dcmd = "bash /open5gs/install/etc/open5gs/5gc_cp_init.sh",
        docker_args = {
            "ports" : { "3000/tcp": 3000 },
            "volumes": {
                PROJECT_FOLDER + "/log": {
                    "bind": "/open5gs/install/var/log/open5gs",
                    "mode": "rw",
                },
                MONGODB_DIR: {
                    "bind": "/var/lib/mongodb",
                    "mode": "rw",
                },
                PROJECT_FOLDER + "/open5gs/config": {
                    "bind": "/open5gs/install/etc/open5gs",
                    "mode": "rw",
                },
                "/etc/timezone": {"bind": "/etc/timezone", "mode": "ro"},
                "/etc/localtime": {"bind": "/etc/localtime", "mode": "ro"},
            },
        },
    )

    info("*** Adding UPFs: Cloud (eMBB), Edge-MEC (URLLC), IoT (mMTC)\n")
    upf_cld = add_upf(net, "upf_cld", "192.168.0.112/24", "upf_cld")
    upf_mec = add_upf(net, "upf_mec", "192.168.0.113/24", "upf_mec")
    upf_iot = add_upf(net, "upf_iot", "192.168.0.114/24", "upf_iot")

    info("*** Adding RAN: 2 gNBs + %d UEs\n" % len(UE_CONFIGS))
    gnb1 = add_ran(net, "gnb1", "192.168.0.131/24")
    gnb2 = add_ran(net, "gnb2", "192.168.0.132/24")
    ue_nodes = []
    for i in range(1, len(UE_CONFIGS) + 1):
        ue_nodes.append(add_ran(net, f"ue{i}", f"192.168.0.{140 + i}/24"))

    info("*** Adding controller and switches\n")
    net.addController("c0")
    s1 = net.addSwitch("s1")   # access    (UEs + gNBs)
    s2 = net.addSwitch("s2")   # edge      (URLLC UPF + control plane)
    s3 = net.addSwitch("s3")   # cloud     (eMBB UPF)
    s4 = net.addSwitch("s4")   # IoT cloud (mMTC UPF)

    info("*** Adding links (shaping on s2-s3 backhaul bottleneck)\n")
    net.addLink(s1, s2, delay = EDGE_DELAY, intfName1 = "s1-s2", intfName2 = "s2-s1")
    net.addLink(s2, s3, bw = BACKHAUL_BW, delay = BACKHAUL_DELAY, max_queue_size = BACKHAUL_QLEN, 
                intfName1 = "s2-s3", intfName2 = "s3-s2")
    net.addLink(s2, s4, delay = BACKHAUL_DELAY, intfName1 = "s2-s4", intfName2 = "s4-s2")
    net.addLink(cp, s2, delay = "1ms", intfName1 = "cp-s2", intfName2 = "s2-cp")
    net.addLink(upf_cld, s3, delay = "1ms", intfName1 = "upf-s3", intfName2 = "s3-upf_cld")
    net.addLink(upf_iot, s4, delay = "1ms", intfName1 = "upf_iot-s4", intfName2 = "s4-upf_iot")
    net.addLink(upf_mec, s2, delay = "1ms", intfName1 = "upf_mec-s2", intfName2 = "s2-upf_mec")
    net.addLink(gnb1, s1, delay = "1ms", intfName1 = "gnb1-s1", intfName2 = "s1-gnb1")
    net.addLink(gnb2, s1, delay = "1ms", intfName1 = "gnb2-s1", intfName2 = "s1-gnb2")

    for i, ue in enumerate(ue_nodes, 1):
        net.addLink(ue, s1, delay = "1ms", intfName1 = f"ue{i}-s1", intfName2 = f"s1-ue{i}")

    print("*** Open5GS: provisioning %d slice subscribers\n" % len (UE_CONFIGS))
    provision_subscribers()

    info("\n*** Starting network\n")
    net.start()

    info("*** Waiting for the AMF NGAP listener (SCTP 38412)\n")
    while "38412" not in cp.cmd("cat /proc/net/sctp/eps"):
        time.sleep(1)

    info("*** Starting gNBs and waiting for NG setup\n")
    for name, yaml in (("gnb1", "open5gs-gnb1.yaml"), ("gnb2", "open5gs-gnb2.yaml")):
        net.get(name).cmd(f"/UERANSIM/build/nr-gnb -c /mnt/ueransim/{yaml} > /mnt/log/{name}.log 2>&1 &")
    for name in ("gnb1", "gnb2"):
        while "successful" not in net.get(name).cmd(
                f"grep -s 'NG Setup procedure is successful' /mnt/log/{name}.log; true"):
            time.sleep(1)
    print("*** Both gNBs registered with the AMF")

    info("*** Starting UEs and waiting for PDU sessions\n")
    for i, ue in enumerate(ue_nodes, 1):
        ue.cmd(f"/UERANSIM/build/nr-ue -c /mnt/ueransim/open5gs-ue{i}.yaml > /mnt/log/ue{i}.log 2>&1 &")
        time.sleep(2)
    for i, ue in enumerate(ue_nodes, 1):
        gw, subnet = SLICE_DN[UE_CONFIGS[i - 1]["sst"]]
        up = False
        for attempt in range(40):
            if "inet" in ue.cmd("ip -4 addr show uesimtun0 2>/dev/null"):
                up = True
                break
            time.sleep(1)
            if attempt == 20:
                print(f"    ue{i}: no session yet, restarting nr-ue...")
                ue.cmd("pkill -9 nr-ue; sleep 1")
                ue.cmd(f"/UERANSIM/build/nr-ue -c /mnt/ueransim/open5gs-ue{i}.yaml > /mnt/log/ue{i}.log 2>&1 &")
        if up:
            ue.cmd(f"ip route replace {subnet} dev uesimtun0")
            ue.cmd(f"ping -c 1 -W 1 {gw} > /dev/null 2>&1")
            print(f"    ue{i}: PDU session up ({subnet} via uesimtun0)")
        else:
            print(f"    ue{i}: \033[91mWARNING: no PDU session after 40s - proceeding\033[0m")

    info("*** Applying mMTC RAN-side rate limit (OVS ingress policing on UE5/UE6)\n")
    # UERANSIM's gNB does not enforce UE-AMBR, so it is emulated here to give the Option-3
    # AMBR test a visible RAN-side cap on the mMTC devices
    s1 = net.get("s1")
    for name in ("ue5", "ue6"):
        port = s1.connectionsTo(net.get(name))[0][0].name
        s1.cmd(f"ovs-vsctl set interface {port} ingress_policing_rate={MMTC_POLICY_KBPS}")
        s1.cmd(f"ovs-vsctl set interface {port} ingress_policing_burst={MMTC_POLICY_BURST}")

    while True:
        main_menu()
        choice = input("  Select an option (0-4): ").strip()

        if choice == "1":
            option1_menu(net)
        elif choice == "2":
            option2_menu(net)
        elif choice == "3":
            option3_menu(net)
        elif choice == "4":
            CLI(net)
        elif choice == "0":
            print("\n  Exiting demo. Shutting down the network...")
            break
        else:
            print("\n  INVALID CHOICE - please try again.")

    net.stop()

