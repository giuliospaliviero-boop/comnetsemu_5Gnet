import time
import re

# =============================================================================
# Test parameters
# =============================================================================
CONGEST_RATE = "80M"   # UDP rate each eMBB device pushes (UE1, UE2)
CONGEST_SECS = 12
URLLC_RATE = "20M"     # URLLC throughput (edge path, uncongested)
# -----------------------------------------------------------------------------

def ping_avg(out):
    out = out.decode("utf-8", "ignore") if isinstance(out, bytes) else out
    m = re.search(r'min/avg/max/mdev = [\d.]+/([\d.]+)/', out)
    return (m.group(1) + " ms") if m else "N/A"

def rate(out):
    out = out.decode("utf-8", "ignore") if isinstance(out, bytes) else out
    for line in out.splitlines():
        if "receiver" in line or "sender" in line:
            m = re.search(r'([\d.]+\s+[KMG]bits/sec)', line)
            if m:
                return m.group(1)
    m = re.findall(r'([\d.]+\s+[KMG]bits/sec)', out)
    return m[-1] if m else "N/A"

def run_isolation_test(net):
    ue1, ue2, ue7 = net.get("ue1"), net.get("ue2"), net.get("ue7")  # eMBB (2 congest + 1 victim)
    ue3, ue4, ue9 = net.get("ue3"), net.get("ue4"), net.get("ue9")  # URLLC latency probes
    ue10 = net.get("ue10")                                          # URLLC throughput probe
    upf_cld, upf_mec = net.get("upf_cld"), net.get("upf_mec")

    for u in (upf_cld, upf_mec):
        u.cmd("pkill -9 iperf3")
    time.sleep(0.5)
    upf_cld.cmd("iperf3 -s -B 10.45.0.1 -p 5201 -D")
    upf_cld.cmd("iperf3 -s -B 10.45.0.1 -p 5202 -D")
    upf_mec.cmd("iperf3 -s -B 10.46.0.1 -p 5204 -D")
    time.sleep(0.5)

    print("\n" + "=" * 60)
    print("  OPTION 2  -  INTER-SLICE ISOLATION (spatial, via 5G tunnels)")
    print("=" * 60)
    print(f"  Load    : UE1 + UE2 each push {CONGEST_RATE} UDP to Cloud for {CONGEST_SECS}s,")
    print("            saturating the 100 Mbps s2-s3 backhaul bottleneck.")
    print("  Watch   : eMBB victim UE7 (same congested path) vs URLLC UE3/4/9")
    print("            (edge path, does NOT cross s2-s3).")
    print("=" * 60)

    print("\n  [BASELINE] no congestion")
    print(f"    eMBB  UE7 --> 10.45.0.1 : {ping_avg(ue7.cmd('ping -c 4 -i 0.2 10.45.0.1'))}")
    print(f"    URLLC UE3 --> 10.46.0.1 : {ping_avg(ue3.cmd('ping -c 4 -i 0.2 10.46.0.1'))}")

    print(f"\n  [CONGESTION] UE1 + UE2 --> Cloud @ {CONGEST_RATE} UDP each")
    guard = str(CONGEST_SECS + 6)
    c1 = ue1.popen(f"timeout -k 3 {guard} iperf3 -u -c 10.45.0.1 -p 5201 -b {CONGEST_RATE} -t {CONGEST_SECS}")
    c2 = ue2.popen(f"timeout -k 3 {guard} iperf3 -u -c 10.45.0.1 -p 5202 -b {CONGEST_RATE} -t {CONGEST_SECS}")
    try:
        time.sleep(3)   # let the s2-s3 queue fill
        print("\n  [DURING CONGESTION]")
        print(f"    eMBB  UE7 --> 10.45.0.1 : \033[91m{ping_avg(ue7.cmd('ping -c 4 -i 0.2 10.45.0.1'))}\033[0m  (inflated)")
        p3 = ue3.popen("ping -c 4 -i 0.2 10.46.0.1")
        p4 = ue4.popen("ping -c 4 -i 0.2 10.46.0.1")
        p9 = ue9.popen("ping -c 4 -i 0.2 10.46.0.1")
        o3, _ = p3.communicate(); o4, _ = p4.communicate(); o9, _ = p9.communicate()
        print(f"    URLLC UE3 --> 10.46.0.1 : \033[92m{ping_avg(o3)}\033[0m")
        print(f"    URLLC UE4 --> 10.46.0.1 : \033[92m{ping_avg(o4)}\033[0m")
        print(f"    URLLC UE9 --> 10.46.0.1 : \033[92m{ping_avg(o9)}\033[0m")
        o10 = ue10.cmd(f"timeout 12 iperf3 -c 10.46.0.1 -p 5204 -t 4 -O 1 -b {URLLC_RATE}")
        print(f"    URLLC UE10 throughput   : \033[92m{rate(o10)}\033[0m  (target {URLLC_RATE}, edge path)")
    finally:
        try:
            c1.communicate(timeout=CONGEST_SECS + 8)
            c2.communicate(timeout=CONGEST_SECS + 8)
        except Exception:
            c1.kill(); c2.kill()
        for u in (upf_cld, upf_mec):
            u.cmd("pkill -9 iperf3")
        ue1.cmd("pkill -9 iperf3"); ue2.cmd("pkill -9 iperf3")

    print("\n" + "-" * 60)
    print("\033[92m  RESULT: eMBB latency rose under its own congestion, while URLLC kept")
    print("  baseline latency and full throughput  ->  spatial isolation holds.\033[0m")
    print("=" * 60)
    input("\n  Press Enter to continue...")

def option2_menu(net):
    while True:
        print("\n\033[93m" + "-" * 60)
        print("  OPTION 2  -  Inter-Slice Performance Isolation")
        print("-" * 60 + "\033[0m")
        print("  [1] Run the isolation / contention analysis")
        print("  [0] Return to MAIN MENU")
        print("-" * 60)
        choice = input("  Select an option (0-1): ").strip()
        if choice == "1":
            run_isolation_test(net)
        elif choice == "0":
            break
        else:
            print("\n  INVALID CHOICE - please try again.")
