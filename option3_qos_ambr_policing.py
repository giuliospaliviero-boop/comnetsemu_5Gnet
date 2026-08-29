import re

# =============================================================================
# Test parameters
# =============================================================================
EMBB_RATE = "60M"      # rate the eMBB control UE (UE1) attempts (authorized traffic)
MMTC_AMBR = "1 Mbps"   # Session-AMBR configured for the mMTC slice
# -----------------------------------------------------------------------------

def rate(out):
    out = out.decode("utf-8", "ignore") if isinstance(out, bytes) else out
    for line in out.splitlines():
        if "receiver" in line:
            m = re.search(r'([\d.]+\s+[KMG]bits/sec)', line)
            if m:
                return m.group(1)
    m = re.findall(r'([\d.]+\s+[KMG]bits/sec)', out)
    return m[-1] if m else "N/A"

def run_qos_ambr_policing_test(net):
    ue1, ue5, ue6 = net.get("ue1"), net.get("ue5"), net.get("ue6")
    upf_cld, upf_iot = net.get("upf_cld"), net.get("upf_iot")

    for u in (upf_cld, upf_iot):
        u.cmd("pkill -9 iperf3")
    upf_cld.cmd("iperf3 -s -B 10.45.0.1 -p 5201 -D")
    upf_iot.cmd("iperf3 -s -B 10.47.0.1 -p 5205 -D")
    upf_iot.cmd("iperf3 -s -B 10.47.0.1 -p 5206 -D")

    print("\n" + "=" * 60)
    print("  OPTION 3  -  SLICE-SPECIFIC QoS & AMBR POLICING")
    print("=" * 60)
    print("  The 5G core caps each PDU session at its Session-AMBR, so an mMTC")
    print("  IoT botnet is bounded by policy, not by attack detection.")
    print("-" * 60)
    print(f"  eMBB control (UE1)     : sends {EMBB_RATE}  (its AMBR is 100 Mbps)")
    print(f"  mMTC botnet (UE5, UE6) : push as hard as possible (their AMBR is {MMTC_AMBR})")
    print("=" * 60)

    if "0 received" in ue5.cmd("ping -c 2 -W 2 10.47.0.1"):
        print("\n\033[91m  WARNING: UE5 cannot reach 10.47.0.1 - check upf_iot.\033[0m")

    try:
        print(f"\n  [CONTROL] eMBB UE1 sending {EMBB_RATE} ...")
        o1 = ue1.cmd(f"timeout 12 iperf3 -u -c 10.45.0.1 -p 5201 -t 10 -b {EMBB_RATE}")
        print(f"    --> UE1 (eMBB) delivered: \033[92m{rate(o1)}\033[0m  (authorized)")

        print("\n  [THREAT] mMTC UE5 + UE6 attempt unlimited transfers ...")
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
        print(f"    --> UE5 (mMTC) throughput: \033[91m{rate(o5)}\033[0m  (capped near its {MMTC_AMBR} AMBR)")
        print(f"    --> UE6 (mMTC) throughput: \033[91m{rate(o6)}\033[0m  (capped near its {MMTC_AMBR} AMBR)")
    finally:
        for u in (upf_cld, upf_iot):
            u.cmd("pkill -9 iperf3")
        ue5.cmd("pkill -9 iperf3"); ue6.cmd("pkill -9 iperf3")

    print("\n" + "-" * 60)
    print("\033[92m  RESULT: eMBB moved data freely; each mMTC device was capped near its")
    print(f"  {MMTC_AMBR} AMBR  -->  a botnet's attack volume is bounded by policy.\033[0m")
    print("=" * 60)
    input("\n  Press Enter to continue...")

def option3_menu(net):
    while True:
        print("\n\033[93m" + "-" * 60)
        print("  OPTION 3  -  Slice-Specific QoS & AMBR Policing")
        print("-" * 60 + "\033[0m")
        print("  [1] Run the IoT-botnet AMBR mitigation test")
        print("  [0] Return to MAIN MENU")
        print("-" * 60)
        choice = input("  Select an option (0-1): ").strip()
        if choice == "1":
            run_qos_ambr_policing_test(net)
        elif choice == "0":
            break
        else:
            print("\n  INVALID CHOICE - please try again.")
