import time
import re

def parse_ping_avg(ping_output):
    # Extract avg latency from ping command.
    if isinstance(ping_output, bytes):
        ping_output = ping_output.decode('utf-8')

    match = re.search(r'rtt min/avg/max/mdev = [\d\.]+/(.*?)/[\d\.]+/', ping_output)
    if match:
        return f"{match.group(1)} ms"
    return "N/A"

def parse_iperf_bw(iperf_output):
    # Extract the receiver bandwidth from iperf3 command.
    if isinstance(iperf_output, bytes):
        iperf_output = iperf_output.decode('utf-8')

    # Find all bandwidth matches and take final summary
    matches = re.findall(r'(\d+(?:\.\d+)?)\s+Mbits/sec', iperf_output)
    if matches:
        return f"{matches[-1]} Mbps"
    return "N/A"

def reset_iperf_servers(upf_cloud, upf_mec):
    # Kills all iperf3 process on-going
    upf_cloud.cmd("pkill -9 iperf3")
    upf_mec.cmd("pkill -9 iperf3")
    time.sleep(0.5)

    # Restarting
    upf_cloud.cmd("iperf3 -s -p 5201 -D")
    upf_cloud.cmd("iperf3 -s -p 5202 -D")
    upf_cloud.cmd("iperf3 -s -p 5203 -D")
    upf_mec.cmd("iperf3 -s -p 5204 -D")
    time.sleep(0.5)

def run_isolation_test(net):
    print("\n" + "="*60)
    time.sleep(0.5)
    #print(" OPTION 2: INTER-SLICE PERFORMANCE ISOLATION")
    #time.sleep(0.5)
    #print("="*60)
    #print("Concept: Demonstrate that traffic congestion in eMBB")
    #print("slice does not degrade the performance of URLLC slice.")
    #print("="*60 + "\n")

    # Define testing nodes
    ue1 = net.get('ue1')     # eMBB device congesting (no.1)
    ue2 = net.get('ue2')     # eMBB device congesting (no.2)
    ue7 = net.get('ue7')     # eMBB measurement device, to sense the network

    ue3 = net.get('ue3')     # URLLC device (no.1)
    ue4 = net.get('ue4')     # URLLC device (no.2)
    ue9 = net.get('ue9')     # URLLC device (no.3)
    ue10 = net.get('ue10')   # URLLC bandwidth test node

    upf_cld = net.get('upf_cld')  # Cloud UPF (eMBB destination)
    upf_mec = net.get('upf_mec')  # Edge UPF (URLLC destination)

    print("[\033[93mPHASE 1\033[0m] Initializing iperf3 traffic...")
    reset_iperf_servers(upf_cld, upf_mec)

    print("\n[\033[96mBASELINE\033[0m] Baseline simulation on URLLC device pings with no congestion...")
    p1_baseline = ue1.popen("ping -c 4 192.168.0.112")
    p2_baseline = ue2.popen("ping -c 4 192.168.0.112")
    p7_baseline = ue7.popen("ping -c 4 192.168.0.112")

    p3_baseline = ue3.popen("ping -c 4 192.168.0.113")
    p4_baseline = ue4.popen("ping -c 4 192.168.0.113")
    p9_baseline = ue9.popen("ping -c 4 192.168.0.113")

    out1_baseline, _ = p1_baseline.communicate()
    out2_baseline, _ = p2_baseline.communicate()
    out7_baseline, _ = p7_baseline.communicate()
    out3_baseline, _ = p3_baseline.communicate()
    out4_baseline, _ = p4_baseline.communicate()
    out9_baseline, _ = p9_baseline.communicate()

    print(f"        -> UE1 (eMBB Device)      baseline latency: \033[93m{parse_ping_avg(out1_baseline)}\033[0m")
    print(f"        -> UE2 (eMBB Device)      baseline latency: \033[93m{parse_ping_avg(out2_baseline)}\033[0m")
    print(f"        -> UE7 (eMBB Device)      baseline latency: \033[93m{parse_ping_avg(out7_baseline)}\033[0m")
    print(f"        -> UE3 (Autonomous Car 1) baseline latency: \033[92m{parse_ping_avg(out3_baseline)}\033[0m")
    print(f"        -> UE4 (Autonomous Car 2) baseline latency: \033[92m{parse_ping_avg(out4_baseline)}\033[0m")
    print(f"        -> UE9 (Autonomous Car 3) baseline latency: \033[92m{parse_ping_avg(out9_baseline)}\033[0m")

    print("[\033[93mPHASE 2\033[0m] Saturating Cloud link with eMBB traffic")
    print("         - UE1 generating 80 Mbps traffic")
    print("         - UE2 generating 80 Mbps traffic")
    p1 = ue1.popen("iperf3 -c 192.168.0.112 -p 5201 -t 5 -b 80M")
    p2 = ue2.popen("iperf3 -c 192.168.0.112 -p 5202 -t 5 -b 80M")
    o1, _ = p1.communicate()
    o2, _ = p2.communicate()
    print(f"        -> UE1 actual bandwidth allocated: \033[93m{parse_iperf_bw(o1)}\033[0m")
    print(f"        -> UE2 actual bandwidth allocated: \033[93m{parse_iperf_bw(o2)}\033[0m")
    reset_iperf_servers(upf_cld, upf_mec)

    print("\n[\033[96mMEASUREMENT A\033[0m] Evaluating eMBB slice latency during congestion...")
    p1 = ue1.popen("iperf3 -c 192.168.0.112 -p 5201 -t 6 -b 80M")
    p2 = ue2.popen("iperf3 -c 192.168.0.112 -p 5202 -t 6 -b 80M")
    time.sleep(1)
    p7_ping = ue7.popen("ping -c 4 192.168.0.112")
    o7_ping, _ = p7_ping.communicate()
    p1.communicate() 
    p2.communicate()
    print(f"        -> eMBB slice latency (from UE7): \033[91m{parse_ping_avg(o7_ping)}\033[0m")
    reset_iperf_servers(upf_cld, upf_mec)

    print("\n[\033[96mMEASUREMENT B\033[0m] Evaluating eMBB UE7 device bandwidth during congestion...")
    p1 = ue1.popen("iperf3 -c 192.168.0.112 -p 5201 -t 10 -b 80M")
    p2 = ue2.popen("iperf3 -c 192.168.0.112 -p 5202 -t 10 -b 80M")
    p7 = ue7.popen("iperf3 -c 192.168.0.112 -p 5203 -t 10 -b 80M")
    o1, _ = p1.communicate()
    o2, _ = p2.communicate()
    o7, _ = p7.communicate()
    print(f"        -> eMBB bandwidth (UE1): \033[91m{parse_iperf_bw(o1)}\033[0m")
    print(f"        -> eMBB bandwidth (UE2): \033[91m{parse_iperf_bw(o2)}\033[0m")
    print(f"        -> eMBB bandwidth (UE7): \033[91m{parse_iperf_bw(o7)}\033[0m")
    reset_iperf_servers(upf_cld, upf_mec)

    print("\n[\033[96mMEASUREMENT C\033[0m] Executing simultaneous URLLC pings during congestion...")
    p1 = ue1.popen("iperf3 -c 192.168.0.112 -p 5201 -t 10 -b 80M")
    p2 = ue2.popen("iperf3 -c 192.168.0.112 -p 5202 -t 10 -b 80M")
    time.sleep(1)
    p3 = ue3.popen("ping -c 4 192.168.0.113")
    p4 = ue4.popen("ping -c 4 192.168.0.113")
    p9 = ue9.popen("ping -c 4 192.168.0.113")

    out3, _ = p3.communicate()
    out4, _ = p4.communicate()
    out9, _ = p9.communicate()
    p1.communicate()
    time.sleep(1)
    p2.communicate()
    time.sleep(1)

    print(f"        -> UE3 (Autonomous Car 1) latency: \033[92m{parse_ping_avg(out3)}\033[0m")
    print(f"        -> UE4 (Autonomous Car 2) latency: \033[92m{parse_ping_avg(out4)}\033[0m")
    print(f"        -> UE9 (Autonomous Car 3) latency: \033[92m{parse_ping_avg(out9)}\033[0m")
    reset_iperf_servers(upf_cld, upf_mec)

    print("\n[\033[96mMEASUREMENT D\033[0m] Verifying URLLC Edge bandwidth...")
    p1 = ue1.popen("iperf3 -c 192.168.0.112 -p 5201 -t 10 -b 80M")
    p2 = ue2.popen("iperf3 -c 192.168.0.112 -p 5202 -t 10 -b 80M")
    p10 = ue10.popen("iperf3 -c 192.168.0.113 -p 5204 -t 10")
    out10, _ = p10.communicate()
    p1.communicate()
    time.sleep(1)
    p2.communicate()
    time.sleep(1)
    print(f"        -> UE10 (URLLC) bandwidth: \033[92m{parse_iperf_bw(out10)}\033[0m")

    print("\n[\033[93mPHASE 3\033[0m] Terminating background traffic flows...")
    upf_cld.cmd("pkill iperf3")
    upf_mec.cmd("pkill iperf3")
    
    print("-" * 60)
    print("\033[92mCONCLUSION: Simulation is terminated\033[0m")
    print("="*60 + "\n")
    
    input("Press Enter to continue...")

def option2_menu(net):
    # Menu for isolation test

    while True:
        print("\n\033[93m" + "-"*50)
        print(" OPTION 2 MENU: Inter-Slice Performance Isolation")
        print("-" * 50 + "\033[0m")
        time.sleep(1)
        print("1. Execute Isolation and Contention Analysis")
        print("0. Return to MAIN MENU")
        print("-" * 50)
        
        choice = input("Select an option (0-1): ")
        
        if choice == '1':
            run_isolation_test(net)
        elif choice == '0':
            print("\nReturning to MAIN MENU...")
            break
        else:
            print("\nINVALID CHOICE! Please try again.")
