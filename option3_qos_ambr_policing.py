import time
import re

def parse_iperf_bw(iperf_output):
    if isinstance(iperf_output, bytes):
        iperf_output = iperf_output.decode('utf-8')
    
    matches = re.findall(r'(\d+(?:\.\d+)?)\s+([KM]bits/sec)', iperf_output)
    if matches:
        value, unit = matches[-1]
        return f"{value} {unit}"
    return "N/A"

def reset_iperf_servers(upf_iot):
    upf_iot.cmd("pkill -9 iperf3")
    time.sleep(0.5)

    upf_iot.cmd("iperf3 -s -p 5201 -D")
    upf_iot.cmd("iperf3 -s -p 5205 -D")
    upf_iot.cmd("iperf3 -s -p 5206 -D")
    time.sleep(0.5)

def run_qos_ambr_policing_test(net):
    print("\n" + "="*65)
    print(" OPTION 3: SLICE-SPECIFIC QoS & AMBR POLICING TEST")
    print("="*65)
    print("Concept: Demonstrate that the 5G core enforces Aggregate")
    print("Maximum Bit Rate (AMBR) profiles. This prevents volumetric")
    print("DDoS attacks that originates from IoT devices.")
    print("="*65 + "\n")

    ue1 = net.get('ue1')
    ue5 = net.get('ue5')
    ue6 = net.get('ue6')
    upf_iot = net.get('upf_iot')

    print("[\033[93mPHASE 1\033[0m] Initializing iperf servers...")
    reset_iperf_servers(upf_iot)

    print("[\033[96mCONTROL TEST\033[0m] eMBB high-bandwidth request...")
    print("               - Physical Link Capacity: 1000 Mbps")
    print("               - UE1 (Smartphone) requesting 200 Mbps stream")
    p1 = ue1.popen("iperf3 -c 192.168.0.114 -p 5201 -t 10 -b 200M")
    out1, _ = p1.communicate()
    print(f"        -> UE1 (eMBB) bandwidth allocated: \033[92m{parse_iperf_bw(out1)}\033[0m (Traffic authorized)")
    reset_iperf_servers(upf_iot)

    print("\n[\033[91mTHREAT DETECTED\033[0m] Emulating Botnet infection on mMTC Slice")
    print("                  - Physical Link Capacity: 1000 Mbps")
    print("                  - UE5 (IoT sensor) infected, requesting \033[91m300 Mbps\033[0m")
    print("                  - UE6 (IoT sensor) infected, requesting \033[91m100 Mbps\033[0m")
    time.sleep(1)

    print("\n[\033[96mMEASUREMENT\033[0m] Evaluating 5G Core AMBR Mitigation...")
    p5 = ue5.popen("iperf3 -c 192.168.0.114 -p 5205 -t 10 -b 300M")
    p6 = ue6.popen("iperf3 -c 192.168.0.114 -p 5206 -t 10 -b 100M")

    out5, _ = p5.communicate()
    out6, _ = p6.communicate()

    print(f"        -> UE5 (mMTC) actual traffic allowed: \033[92m{parse_iperf_bw(out5)}\033[0m")
    print(f"        -> UE6 (mMTC) actual traffic allowed: \033[92m{parse_iperf_bw(out6)}\033[0m")

    print("\n[\033[93mPHASE 3\033[0m] Terminating traffic flows...")
    upf_iot.cmd("pkill -9 iperf3")

    print("-" * 65)
    print("\033[92mSIMULATION TERMINATED\033[0m")
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

        if choice == '1':
            run_qos_ambr_policing_test(net)
        elif choice == '0':
            break
        else:
            print("\nINVALID CHOICE. Please try again...")


