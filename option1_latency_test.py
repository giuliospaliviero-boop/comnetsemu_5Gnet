import time
import re

UE_INFO = {
    1: {"type": "eMBB", "upf_name": "Cloud UPF", "upf_ip": "192.168.0.112"},
    2: {"type": "eMBB", "upf_name": "Cloud UPF", "upf_ip": "192.168.0.112"},
    3: {"type": "URLLC", "upf_name": "Edge MEC UPF", "upf_ip": "192.168.0.113"},
    4: {"type": "URLLC", "upf_name": "Edge MEC UPF", "upf_ip": "192.168.0.113"},
    5: {"type": "mMTC", "upf_name": "Cloud UPF", "upf_ip": "192.168.0.112"},
    6: {"type": "mMTC", "upf_name": "Cloud UPF", "upf_ip": "192.168.0.112"},
    7: {"type": "eMBB", "upf_name": "Cloud UPF", "upf_ip": "192.168.0.112"},
    8: {"type": "eMBB", "upf_name": "Cloud UPF", "upf_ip": "192.168.0.112"},
    9: {"type": "URLLC", "upf_name": "Edge MEC UPF", "upf_ip": "192.168.0.113"},
    10: {"type": "URLLC", "upf_name": "Edge MEC UPF", "upf_ip": "192.168.0.113"},
}

def parse_ping_avg(ping_output):
    # Helper function to extract the average latency from a ping command output.
    # Skip min value, save the corresponding avg value with .*? instruction and
    # discard the max and mdev values.
    match = re.search(r'rtt min/avg/max/mdev = [\d\.]+/(.*?)/[\d\.]+/', ping_output)
    if match:
        return f"{match.group(1)} ms"
    return "N/A"

def run_single_test(net, ue_id):
    # Executes latency test (ping) for the selected device.
    info = UE_INFO[ue_id]
    ue_name = f"ue{ue_id}"
    ue_node = net.get(ue_name)

    print("\n" + "="*60)
    time.sleep(0.5)
    print(f" TESTING {ue_name.upper()} ({info['type']} Slice)")
    time.sleep(0.5)
    print("="*60)
    time.sleep(0.5)
    print(f"Routing expected to: {info['upf_name']} ({info['upf_ip']})")
    time.sleep(0.5)
    print("Pinging...")

    time.sleep(1)
    output = ue_node.cmd(f"ping -c 6 {info['upf_ip']}")
    avg_latency = parse_ping_avg(output)

    if info['type'] == "URLLC":
        print(f"-> Average Latency: \033[92m{avg_latency}\033[0m (Ultra-Low Latency Edge)")
    else:
        print(f"-> Average Latency: \033[93m{avg_latency}\033[0m (Standard Cloud Latency)")
    print("="*60 + "\n")

    input("Press Enter to continue...")

'''def run_test(net):
    print("\n" + "="*60)
    #print(" OPTION 1: EDGE VS. CLOUD LATENCY PROOF (Routing)")
    print(" OPTION 1: LATENCY TESTS ")
    print("="*60)
    #print("Concept: Prove that the 5G Core physically routes URLLC")
    #print("traffic to the Edge (MEC) and eMBB traffic to the Cloud.\n")
    
    ue1 = net.get('ue1') # eMBB UE
    ue9 = net.get('ue9') # URLLC UE

    print("[\033[96mTEST 1\033[0m] Pinging Central Cloud UPF from UE1 (eMBB Slice)...")
    time.sleep(1)
    embb_output = ue1.cmd('ping -c 4 192.168.0.112')
    embb_avg = parse_ping_avg(embb_output)
    print(f"         -> eMBB Average Latency: \033[93m{embb_avg}\033[0m")

    time.sleep(1)
    print("\n[\033[96mTEST 2\033[0m] Pinging Edge MEC UPF from UE9 (URLLC Slice)...")
    time.sleep(1)
    urllc_output = ue9.cmd('ping -c 4 192.168.0.113')
    urllc_avg = parse_ping_avg(urllc_output)
    print(f"         -> URLLC Average Latency: \033[92m{urllc_avg}\033[0m\n")

    print("-" * 60)
    print("\033[92mRESULT: SUCCESS!\033[0m")
    print("The SMF successfully isolated the URLLC traffic, bypassing")
    print("the 40ms cloud link and keeping latency ultra-low at the Edge.")
    print("="*60 + "\n")
    
    input("Press Enter to continue...")'''

def option1_menu(net):
    # Menu for latency test
    while True:
        print("\n\033[94m" + "-"*45)
        print(" OPTION 1 MENU: Edge vs. Cloud Latency")
        print("-" * 45 + "\033[0m")
        print("Select a device (UE) to test its latency to the core network:")
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

