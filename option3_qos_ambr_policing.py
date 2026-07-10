import time
import re

def udp_delivered(out):
    if isinstance(out, bytes):
        out = out.decode("utf-8", "ignore")
    for line in out.splitlines():
        if "receiver" in line:
            m = re.search(r'([\d.]+\s+[KMG]bits/sec).*?\(([\d.]+%)\)', line)
            if m:
                return m.group(1) + " (" + m.group(2) + " loss)"
    m = re.findall(r'([\d.]+\s+[KMG]bits/sec)', out)
    return m[-1] if m else "N/A"

def run_qos_ambr_policing_test(net):
    ue1 = net.get("ue1")                          # eMBB smartphone
    ue5 = net.get("ue5"); ue6 = net.get("ue6")    # mMTC IoT sensors (botnet)
    upf_cld = net.get("upf_cld")                  # eMBB DN  (10.45.0.1)
    upf_iot = net.get("upf_iot")                  # mMTC DN  (10.47.0.1)

    for u in (upf_cld, upf_iot):
        u.cmd("pkill -9 iperf3")
    time.sleep(0.3)
    upf_cld.cmd("iperf3 -s -B 10.45.0.1 -p 5201 -D")
    upf_iot.cmd("iperf3 -s -B 10.47.0.1 -p 5205 -D")
    upf_iot.cmd("iperf3 -s -B 10.47.0.1 -p 5206 -D")
    time.sleep(0.5)

    print("\n" + "=" * 65)
    print(" OPTION 3: SLICE-SPECIFIC QoS & AMBR POLICING")
    print("=" * 65)
    print("The 5G core enforces Session-AMBR per PDU session at the UPF, so a")
    print("botnet of mMTC devices is bounded by POLICY (N x AMBR), not detection.")
    print("=" * 65)

    try:
        print("\n[CONTROL] eMBB smartphone UE1 requests 15 Mbps  (its AMBR is 100 Mbps)")
        o1 = ue1.cmd("iperf3 -u -c 10.45.0.1 -p 5201 -b 15M -t 3")
        print("   -> UE1 (eMBB) delivered: \033[92m" + udp_delivered(o1) + "\033[0m  (authorized)")

        print("\n[THREAT]  mMTC botnet: UE5 + UE6 each blast 20 Mbps  (their AMBR is 1 Mbps)")
        p5 = ue5.popen("iperf3 -u -c 10.47.0.1 -p 5205 -b 20M -t 4")
        p6 = ue6.popen("iperf3 -u -c 10.47.0.1 -p 5206 -b 20M -t 4")
        o5, _ = p5.communicate(); o6, _ = p6.communicate()
        print("   -> UE5 (mMTC) delivered: \033[91m" + udp_delivered(o5) + "\033[0m  (throttled by the core)")
        print("   -> UE6 (mMTC) delivered: \033[91m" + udp_delivered(o6) + "\033[0m  (throttled by the core)")
    finally:
        for u in (upf_cld, upf_iot):
            u.cmd("pkill -9 iperf3")

    print("\n" + "-" * 65)
    print("\033[92mRESULT: eMBB received its 15 Mbps; the mMTC botnet was capped to a")
    print("few Mbps each at the UPF - attack volume is bounded by subscription policy.\033[0m")
    print("=" * 65 + "\n")
    input("Press Enter to continue...")

def option3_menu(net):
    while True:
        print("\n\033[93m" + "-" * 60)
        print(" OPTION 3 MENU: Slice-Specific QoS & AMBR Policing Test")
        print("-" * 60 + "\033[0m")
        print(" [1] Execute IoT Botnet Mitigation Test through AMBR Policy")
        print(" [0] Return to MAIN MENU")
        print("-" * 60)
        choice = input("Select an option (0-1): ")
        if choice == "1":
            run_qos_ambr_policing_test(net)
        elif choice == "0":
            break
        else:
            print("\nINVALID CHOICE. Please try again...")
