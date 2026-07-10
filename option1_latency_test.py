import time
import re

UE_INFO = {
    1: {"type": "eMBB", "upf_name": "Cloud UPF (DN 'internet')", "target": "10.45.0.1", "expected": "~90 ms"},
    2: {"type": "eMBB", "upf_name": "Cloud UPF (DN 'internet')", "target": "10.45.0.1", "expected": "~90 ms"},
    3: {"type": "URLLC", "upf_name": "Edge MEC UPF (DN 'mec')", "target": "10.46.0.1", "expected": "~9 ms"},
    4: {"type": "URLLC", "upf_name": "Edge MEC UPF (DN 'mec')", "target": "10.46.0.1", "expected": "~9 ms"},
    5: {"type": "mMTC", "upf_name": "IoT Cloud UPF (DN 'iot')", "target": "10.47.0.1", "expected": "~90 ms"},
    6: {"type": "mMTC", "upf_name": "IoT Cloud UPF (DN 'iot')", "target": "10.47.0.1", "expected": "~90 ms"},
    7: {"type": "eMBB", "upf_name": "Cloud UPF (DN 'internet')", "target": "10.45.0.1", "expected": "~90 ms"},
    8: {"type": "eMBB", "upf_name": "Cloud UPF (DN 'internet')", "target": "10.45.0.1", "expected": "~90 ms"},
    9: {"type": "URLLC", "upf_name": "Edge MEC UPF (DN 'mec')", "target": "10.46.0.1", "expected": "~9 ms"},
    10: {"type": "URLLC", "upf_name": "Edge MEC UPF (DN 'mec')", "target": "10.46.0.1", "expected": "~9 ms"},
}

def parse_ping_avg(ping_output):
    # Helper function to extract the average latency from a ping command output.
    # Skip min value, save the corresponding avg value with .*? instruction and
    # discard the max and mdev values.
    if isinstance(ping_output, bytes):
        ping_output = ping_output.decode('utf-8')
    match = re.search(r'rtt min/avg/max/mdev = [\d\.]+/(.*?)/[\d\.]+/', ping_output)
    if match:
        return f"{match.group(1)} ms"
    return "N/A"

def run_single_test(net, ue_id):
    # Executes latency test (ping) for the selected device.
    ue_info = UE_INFO[ue_id]
    #ue_name = f"ue{ue_id}"
    ue_name = "ue" + str(ue_id)
    ue_node = net.get(ue_name)

    print("\n" + "="*60)
    print(f" TESTING {ue_name.upper()} ({ue_info['type']} Slice)")
    print("="*60)

    # Check if the PDU session is up
    if "inet" not in ue_node.cmd("ip -4 addr show uesimtun0 2>/dev/null"):
        print("\033[91mERROR: no uesimtun0 - PDU session not established for this UE.\033[0m")
        input("Press Enter to continue...")
        return

    print(f"PDU session anchor: {ue_info['upf_name']} --> pinging {ue_info['target']} over GTP-U")
    print(f"Expected RTT: {ue_info['expected']}")

    # Warm-up ping (for cleaner measurements)
    #ue_node = ue_node.cmd(f"ping -c 1 W 1 {ue_info['target']} > /dev/null 2>&1")

    #output = ue_node.cmd(f"ping -c 6 {ue_info['target']}")
    output = ue_node.cmd("ping -c 6 " + ue_info["target"])
    avg_latency = parse_ping_avg(output)

    if ue_info["type"] == "URLLC":
        print(f"-> Average Latency: \033[92m{avg_latency}\033[0m (Ultra-Low Latency Edge)")
    else:
        print(f"-> Average Latency: \033[93m{avg_latency}\033[0m (Standard Cloud Latency)")
    print("="*60 + "\n")

    input("Press Enter to continue...")


def option1_menu(net):
    # Menu for latency test
    while True:
        print("\n\033[94m" + "-"*45)
        print(" OPTION 1 MENU: Edge vs. Cloud Latency (via 5G tunnel)")
        print("-" * 45 + "\033[0m")
        print("Select a device (UE) to test its latency to its slice's Data Network:")
        print("  [1, 2, 7, 8]  : eMBB UEs (High Bandwidth Applications)")
        print("  [3, 4, 9, 10] : URLLC UEs (Autonomous Cars)")
        print("  [5, 6]        : mMTC UEs (IoT Sensors)")
        print("  [0]           : Return to MAIN MENU")
        print("-" * 50)

        choice = input("Select an option (0-10): ")

        try:
            ue_id = int(choice)
            if ue_id == 0:
                print("\nReturning to MAIN MENU...")
                time.sleep(1)
                break
            elif 1 <= ue_id <= 10:
                run_single_test(net, ue_id)
            else:
                print("\nINVALID CHOICE! Please enter a number between 0 and 10.")
        except ValueError:
            print("\nINVALID INPUT. Only numbers accepted. Try again...")

