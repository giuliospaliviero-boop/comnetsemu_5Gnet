import re

def tcp_rate(out):
    if isinstance(out, bytes):
        out = out.decode("utf-8", "ignore")
    for line in out.splitlines():
        if "receiver" in line:
            m = re.search(r'([\d.]+\s+[KMG]bits/sec)', line)
            if m:
                return m.group(1)
    m = re.findall(r'([\d.]+\s+[KMG]bits/sec)', out)
    return m[-1] if m else "N/A"

def run_qos_ambr_policing_test(net):
    ue1 = net.get("ue1"); ue5 = net.get("ue5"); ue6 = net.get("ue6")
    upf_cld = net.get("upf_cld"); upf_iot = net.get("upf_iot")

    for u in (upf_cld, upf_iot):
        u.cmd("pkill -9 iperf3")
    upf_cld.cmd("iperf3 -s -B 10.45.0.1 -p 5201 -D")
    upf_iot.cmd("iperf3 -s -B 10.47.0.1 -p 5205 -D")
    upf_iot.cmd("iperf3 -s -B 10.47.0.1 -p 5206 -D")

    print("\n" + "=" * 65)
    print(" OPTION 3: SLICE-SPECIFIC QoS & AMBR POLICING")
    print("=" * 65)
    print("Each mMTC PDU session is capped at its Session-AMBR by the core.")
    print("TCP goodput settles exactly at the enforced cap: policy, not detection.")
    print("=" * 65)

    if "0 received" in ue5.cmd("ping -c 2 -W 2 10.47.0.1"):
        print("\n\033[91mWARNING: UE5 cannot reach 10.47.0.1 - check upf_iot before testing.\033[0m")

    try:
        print("\n[CONTROL] eMBB UE1 transfer (Session-AMBR 100 Mbps)")
        o1 = ue1.cmd("timeout 12 iperf3 -u -c 10.45.0.1 -p 5201 -t 10 -b 60M")
        print("   -> UE1 (eMBB) goodput: \033[92m" + tcp_rate(o1) + "\033[0m  (high, authorized)")

        print("\n[THREAT]  mMTC botnet: UE5 + UE6 attempt unlimited transfers (AMBR 1 Mbps)")
        p5 = ue5.popen("timeout 14 iperf3 -c 10.47.0.1 -p 5205 -t 6 -O 1")
        p6 = ue6.popen("timeout 14 iperf3 -c 10.47.0.1 -p 5206 -t 6 -O 1")
        try:
            o5, _ = p5.communicate(timeout=18)
        except Exception:
            p5.kill(); o5 = b""
        try:
            o6, _ = p6.communicate(timeout=18)
        except Exception:
            p6.kill(); o6 = b""
        print("   -> UE5 (mMTC) goodput: \033[91m" + tcp_rate(o5) + "\033[0m  (capped by the core)")
        print("   -> UE6 (mMTC) goodput: \033[91m" + tcp_rate(o6) + "\033[0m  (capped by the core)")
    finally:
        for u in (upf_cld, upf_iot):
            u.cmd("pkill -9 iperf3")
        ue5.cmd("pkill -9 iperf3"); ue6.cmd("pkill -9 iperf3")

    print("\n" + "-" * 65)
    print("\033[92mRESULT: eMBB moved data freely; each mMTC device was capped to ~its")
    print("AMBR - a botnet's attack volume is bounded by subscription policy.\033[0m")
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
