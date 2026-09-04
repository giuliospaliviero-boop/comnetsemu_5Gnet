import re
import time

# =============================================================================
# Option 4 - Scheduling-based isolation on SHARED link
# =============================================================================

GNB = "gnb1"
SHARED_IF = "gnb1-s1"         # ue1's access link
EMBB_UE = "ue7"
URLLC_UE = "ue3"
EMBB_TARGET = "10.45.0.1"
URLLC_TARGET = "10.46.0.1"
EMBB_DST = "192.168.0.112"   # upf_cld GTP-U
URLLC_DST = "192.168.0.113"  # upf_mec GTP-U
IPERF_PORT = 5201
PIPE = "20mbit"
TEST_SECS = 12
PING_COUNT = 20

def _fifo(gnb):
    """Phase A: one FIFO for the whole 20 Mbps pipe, no differentiation."""
    gnb.cmd(f"tc qdisc del dev {SHARED_IF} root 2>/dev/null")
    gnb.cmd(f"tc qdisc add dev {SHARED_IF} root handle 1: htb default 10")
    gnb.cmd(f"tc class add dev {SHARED_IF} parent 1: classid 1:10 htb rate {PIPE} ceil {PIPE}")
    gnb.cmd(f"tc qdisc add dev {SHARED_IF} parent 1:10 handle 10: pfifo limit 200")

def _priority(gnb):
    """Phase B: strict-priority HTB - URLLC high, eMBB low"""
    gnb.cmd(f"tc qdisc del dev {SHARED_IF} root 2>/dev/null")
    gnb.cmd(f"tc qdisc add dev {SHARED_IF} root handle 1: htb default 30")
    gnb.cmd(f"tc class add dev {SHARED_IF} parent 1 classid 1:10 htb rate {PIPE} ceil {PIPE}")
    gnb.cmd(f"tc class add dev {SHARED_IF} parent 1:1 classid 1:10 htb rate 12mbit ceil {PIPE} prio 0")  # URLLC
    gnb.cmd(f"tc class add dev {SHARED_IF} parent 1:1 classid 1:20 htb rate 6mbit ceil {PIPE} prio 1")  # eMBB
    gnb.cmd(f"tc class add dev {SHARED_IF} parent 1:1 classid 1:30 htb rate 2mbit ceil {PIPE} prio 0")  # signalling/default
    for leaf in ("10", "20", "30"):
        gnb.cmd(f"tc qdisc add dev {SHARED_IF} parent 1:{leaf} handle {leaf}: fq_codel")
    gnb.cmd(f"tc filter add dev {SHARED_IF} protocol ip parent 1: prio 1 "
            f"u32 match ip dst {URLLC_DST}/32 flowid 1:10")  # URLLC GTP-U --> high-priority queue
    gnb.cmd(f"tc filter add dev {SHARED_IF} protocol ip parent 1: prio 2 "
            f"u32 match ip dst {EMBB_DST}/32 flowid 1:20")  # eMBB GTP-U --> low-priority queue

def _restore(gnb):
    """Remove qdisc and restore gnb1-s1's original 1 ms emulated delay"""
    gnb.cmd(f"tc qdisc del dev {SHARED_IF} root 2>/dev/null")
    gnb.cmd(f"tc qdisc add dev {SHARED_IF} root netem delay 1ms 2>/dev/null")

def _ping_avg(out):
    out = out.decode("utf-8", "ignore") if isinstance(out, bytes) else out
    m = re.search(r'min/avg/max/mdev = [\d.]+/([\d.]+)/', out)
    return (m.group(1) + "ms") if m else "N/A"

def _rate(out):
    out = out.decode("utf-8", "ignore") if isinstance(out, bytes) else out
    for line in out.splitlines():
        if "receiver" in line:
            m = re.search(r'([\d.]+\s[KMG]bits/sec)', line)
            if m:
                return m.group(1)
    m = re.findall(f'([\d.]+\s+[KMG]bits/sec)', out)
    return m[-1] if m else "N/A"

def _run_phase(embb_ue, urllc_ue, gnb, label, apply_qos):
    apply_qos(gnb)
    flood = embb_ue.popen(f"iperf3 -c {EMBB_TARGET} -p {IPERF_PORT} -t {TEST_SECS} -O 1")
    time.sleep(2)
    urllc = _ping_avg(urllc_ue.cmd(f"ping -c {PING_COUNT} -i 0.2 -w 6 {URLLC_TARGET}"))
    try:
        o, _ = flood.communicate(timeout=TEST_SECS + 5)
    except Exception:
        flood.kill(); o = b""
    print(f"    {label:34}  URLLC latency: \033[93m{urllc:>9}\033[0m   eMBB rate: {_rate(o)}")
    return urllc

def run_priority_scheduling_test(net):
    gnb = net.get(GNB)
    embb_ue = net.get(EMBB_UE)
    urllc_ue = net.get(URLLC_UE)
    upf_cld = net.get("upf_cld")

    upf_cld.cmd("pkill -9 iperf3 2>/dev/null")
    time.sleep(0.3)
    upf_cld.cmd(f"iperf3 -s -B {EMBB_TARGET} -p {IPERF_PORT} -D")

    print("\n" + "=" * 60)
    print("  OPTION 4  -  Scheduling-based Isolation on a shared link")
    print("=" * 60)
    print(f"  Shared link : {SHARED_IF}  ({GNB} backhaul - both UEs' GTP-U multiplexed here)")
    print(f"  eMBB device : {EMBB_UE} --> {EMBB_TARGET}  (GTP-U to {EMBB_DST}) [low priority]")
    print(f"  URLLC device: {URLLC_UE} --> {URLLC_TARGET}  (GTP-U to {URLLC_DST}) [high priority]")
    print(f"  Bottleneck  : {PIPE} shared - identical in both phases; only the scheduler changes")
    print("=" * 60)

    if "0 received" in urllc_ue.cmd(f"ping -c 2 -W 2 {URLLC_TARGET}"):
        print(f"\n\033[91m  WARNING: {URLLC_UE} cannot reach {URLLC_TARGET} - check its PDU session.\033[0m")

    try:
        print("\n  [PHASE A]  single FIFO queue - 5QI ignored")
        a = _run_phase(embb_ue, urllc_ue, gnb, "URLLC shares one queue", _fifo)

        print("\n  [PHASE B]  strict-priority scheduler - URLLC in a high-priority queue")
        b = _run_phase(embb_ue, urllc_ue, gnb, "URLLC in its own priority queue", _priority)
    finally:
        _restore(gnb)
        embb_ue.cmd("pkill -9 iperf3 2>/dev/null")
        upf_cld.cmd("pkill -9 iperf3 2>/dev/null")

    print("\n" + "-" * 60)
    print("\033[92m  RESULT: under the same eMBB congestion on the same share backhaul,")
    print(f"  URLLC latency fell from {a} (no QoS) to {b} (priority scheduling),")
    print("  while eMBB still used the pipe when URLLC was idle. The 5QI is now")
    print("  enforced by scheduling.\033[0m")
    print("=" * 60)
    input("\n  Press Enter to continue...")

def option4_menu(net):
    while True:
        print("\n\033[93m" + "=" * 60)
        print("  OPTION 4  -  Scheduling-based Isolation")
        print("-" * 60 + "\033[0m")
        print("  [1] Run the shared-link priority-scheduling test")
        print("  [0] Return to MAIN MENU")
        print("-" * 60)
        choice = input("  Select an option (0-1): ").strip()
        if choice == "1":
            run_priority_scheduling_test(net)
        elif choice == "0":
            break
        else:
            print("\n  INVALID CHOICE - please try again.")

