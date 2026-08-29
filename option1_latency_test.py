import re

# Each UE pings the ogstun (Data Network) address of its slice's UPF, so the
# ICMP traverses the real 5G user plane: uesimtun0 --> RLS --> gNB --> GTP-U --> UPF
SLICE_TARGET = {               # slice --> (DN gateway, UPF label, colour)
    "eMBB": ("10.45.0.1", "Cloud UPF (internet)", "93"),
    "URLLC": ("10.46.0.1", "Edge MEC UPF (mec)", "92"),
    "mMTC": ("10.47.0.1", "IoT UPF (iot)", "93"),
}
UE_SLICE = {1: "eMBB", 2: "eMBB", 3: "URLLC", 4: "URLLC", 5: "mMTC",
            6: "mMTC", 7: "eMBB", 8: "eMBB", 9: "URLLC", 10: "URLLC"}
PING_COUNT = 20

def parse_ping(out):
    out = out.decode("utf-8", "ignore") if isinstance(out, bytes) else out
    m = re.search(r'min/avg/max/mdev = ([\d.]+)/([\d.]+)/[\d.]+/([\d.]+)', out)
    return (m.group(1), m.group(2), m.group(3)) if m else None

def run_single_test(net, ue_id):
    slice_name = UE_SLICE[ue_id]
    target, upf, colour = SLICE_TARGET[slice_name]
    ue = net.get(f"ue{ue_id}")

    print("\n" + "=" * 60)
    print(f"  LATENCY TEST  -  UE{ue_id}  [{slice_name} slice]")
    print("=" * 60)
    print(f"  Anchor  : {upf}")
    print(f"  Target  : {target}   (through the GTP-U tunnel)")
    print(f"  Samples : {PING_COUNT} pings, first discarded (ARP warm-up)")
    print("-" * 60)

    ue.cmd(f"ping -c 1 -W 1 {target} >/dev/null 2>&1")              # discard first packet
    res = parse_ping(ue.cmd(f"ping -c {PING_COUNT} -i 0.2 {target}"))
    if res:
        mn, avg, jit = res
        print(f"  --> min \033[{colour}m{mn} ms\033[0m  avg {avg} ms  jitter {jit} ms")
        print("      (min RTT is the stable path latency due to emulator overhead (jitter))")
    else:
        print("  --> \033[91mno reply - check this UE's PDU session\033[0m")
    print("=" * 60)
    input("\n  Press Enter to continue...")

def option1_menu(net):
    while True:
        print("\n\033[94m" + "-" * 60)
        print("  OPTION 1  -  Edge vs. Cloud Latency (per-UE, via 5G tunnel)")
        print("-" * 60 + "\033[0m")
        print("  eMBB  UEs [1, 2, 7, 8]   -> Cloud   (~100 ms, high-bandwidth apps)")
        print("  URLLC UEs [3, 4, 9, 10]  -> Edge    (~20 ms,  autonomous cars)")
        print("  mMTC  UEs [5, 6]         -> IoT     (~100 ms, sensors)")
        print("  [0] Return to MAIN MENU")
        print("-" * 60)
        choice = input("  Select a UE (0-10): ").strip()
        if choice == "0":
            return
        if choice.isdigit() and 1 <= int(choice) <= 10:
            run_single_test(net, int(choice))
        else:
            print("\n  INVALID CHOICE - enter a number 0-10.")

