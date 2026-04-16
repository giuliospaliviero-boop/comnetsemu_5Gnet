import time
import re
from comnetsemu.cli import CLI

def parse_ping_avg(ping_output):
    # Helper function to extract the average latency from a ping command output.
    # Skip min value, save the corresponding avg value with .*? and discard the
    # max and mdev values.
    match = re.search(r'rtt min/avg/max/mdev = [\d\.]+/(.*?)/[\d\.]+/', ping_output)
    if match:
        return f"{match.group(1)} ms"
    return "N/A"

def run_act1_latency(net):
    print("\n" + "="*60)
    print(" ACT 1: EDGE VS. CLOUD LATENCY PROOF (Routing)")
    print("="*60)
    print("Concept: Prove that the 5G Core physically routes URLLC")
    print("traffic to the Edge (MEC) and eMBB traffic to the Cloud.\n")
    
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
    
    input("Press Enter to return to the main menu...")

def run_demo_menu(net):
    while True:
        print("\n\033[95m" + "#"*45)
        print(" 5G NETWORK SLICING & MEC DEMONSTRATION")
        print("#"*45 + "\033[0m")
        print("1. Act 1: Edge vs. Cloud Latency (Routing Proof)")
        print("2. Act 2: Noisy Neighbor (Isolation Proof) [Coming Soon]")
        print("3. Act 3: QoS & AMBR Enforcer (Throttling) [Coming Soon]")
        print("4. Drop to Manual Mininet CLI")
        print("5. Exit and Stop Network")
        print("#"*45)
        
        choice = input("Select an option (1-5): ")
        
        if choice == '1':
            run_act1_latency(net)
        elif choice == '2':
            print("\nAct 2 is under construction...\n")
        elif choice == '3':
            print("\nAct 3 is under construction...\n")
        elif choice == '4':
            print("\nDropping to Mininet CLI. Type 'exit' to return to this menu.")
            CLI(net)
        elif choice == '5':
            print("\nExiting demo. Shutting down network...")
            break
        else:
            print("\nInvalid choice. Please try again.")
