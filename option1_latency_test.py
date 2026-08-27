import re

UE_INFO = {
    1:  {"type": "eMBB",  "upf_name": "Cloud UPF (DN 'internet')", "target": "10.45.0.1", "expected": "~100 ms"},
    2:  {"type": "eMBB",  "upf_name": "Cloud UPF (DN 'internet')", "target": "10.45.0.1", "expected": "~100 ms"},
    3:  {"type": "URLLC", "upf_name": "Edge MEC UPF (DN 'mec')",   "target": "10.46.0.1", "expected": "~20 ms"},
    4:  {"type": "URLLC", "upf_name": "Edge MEC UPF (DN 'mec')",   "target": "10.46.0.1", "expected": "~20 ms"},
    5:  {"type": "mMTC",  "upf_name": "IoT Cloud UPF (DN 'iot')",  "target": "10.47.0.1", "expected": "~100 ms"},
    6:  {"type": "mMTC",  "upf_name": "IoT Cloud UPF (DN 'iot')",  "target": "10.47.0.1", "expected": "~100 ms"},
    7:  {"type": "eMBB",  "upf_name": "Cloud UPF (DN 'internet')", "target": "10.45.0.1", "expected": "~100 ms"},
    8:  {"type": "eMBB",  "upf_name": "Cloud UPF (DN 'internet')", "target": "10.45.0.1", "expected": "~100 ms"},
    9:  {"type": "URLLC", "upf_name": "Edge MEC UPF (DN 'mec')",   "target": "10.46.0.1", "expected": "~20 ms"},
    10: {"type": "URLLC", "upf_name": "Edge MEC UPF (DN 'mec')",   "target": "10.46.0.1", "expected": "~20 ms"},
}

def parse_ping_avg(out):
    if isinstance(out, bytes):
        out = out.decode("utf-8", "ignore")
    m = re.search(r'min/avg/max/mdev = [\d.]+/([\d.]+)/', out)
    return (m.group(1) + " ms") if m else "N/A"

def run_single_test(net, ue_id):
    ue_info = UE_INFO[ue_id]
    ue_node = net.get("ue" + str(ue_id))

    print("\n" + "=" * 60)
    print(" TESTING UE" + str(ue_id) + " (" + ue_info["type"] + " Slice)")
    print("=" * 60)
    print("PDU session anchor: " + ue_info["upf_name"]
          + " -> pinging " + ue_info["target"] + " over GTP-U")
    print("Expected RTT: " + ue_info["expected"])

    output = ue_node.cmd("ping -c 6 " + ue_info["target"])
    avg = parse_ping_avg(output)
    color = "92" if ue_info["type"] == "URLLC" else "93"
    label = "(Ultra-Low Latency Edge)" if ue_info["type"] == "URLLC" else "(Standard Cloud Latency)"
    print("-> Average Latency: \033[" + color + "m" + avg + "\033[0m " + label)
    print("=" * 60 + "\n")
    input("Press Enter to continue...")

def option1_menu(net):
    while True:
        print("\n\033[94m" + "-" * 45)
        print(" OPTION 1 MENU: Edge vs. Cloud Latency (via 5G tunnel)")
        print("-" * 45 + "\033[0m")
        print("  [1, 2, 7, 8]  : eMBB UEs (High Bandwidth Applications)")
        print("  [3, 4, 9, 10] : URLLC UEs (Autonomous Cars)")
        print("  [5, 6]        : mMTC UEs (IoT Sensors)")
        print("  [0]           : Return to MAIN MENU")
        print("-" * 50)
        choice = input("Select an option (0-10): ")
        try:
            ue_id = int(choice)
            if ue_id == 0:
                break
            elif 1 <= ue_id <= 10:
                run_single_test(net, ue_id)
            else:
                print("\nINVALID CHOICE! Enter a number between 0 and 10.")
        except ValueError:
            print("\nINVALID INPUT. Only numbers accepted.")
