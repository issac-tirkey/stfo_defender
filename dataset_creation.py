# import time
# import pandas as pd
# from scapy.all import rdpcap, sendp
# import subprocess
# from threading import Thread
#
# interface = 's1-eth1'
#
#
# def collect_flow_data(switch, label, output_file):
#     flow_data = {
#         'timestamp': time.time(),
#         'flow_entry_duration': None,  # Placeholder for actual duration data
#         'number_of_bytes': None,  # Placeholder for actual byte count
#         'number_of_packets': None,  # Placeholder for actual packet count
#         'src_ip': None,  # Placeholder for actual source IP
#         'dst_ip': None,  # Placeholder for actual destination IP
#         'src_port': None,  # Placeholder for actual source port
#         'dst_port': None,
#         'label': label
#     }
#
#     df = pd.DataFrame([flow_data])
#     with open(output_file, 'a') as f:
#         df.to_csv(f, header=f.tell() == 0, index=False)
#
#
# def replay_and_collect(pcap_file, attack_script, output_file, switch='s1'):
#     # Read the packets from the pcap file
#     packets = rdpcap(pcap_file)
#
#     def replay_packets():
#         sendp(packets, iface=interface, inter=0.01, loop=0, verbose=False)
#
#     def collect_data(duration, attack_launched):
#         start_time = time.time()
#         while time.time() - start_time < duration:
#             label = 1 if attack_launched and time.time() - start_time >= 80 else 0
#             collect_flow_data(switch, label, output_file)
#             time.sleep(1)  # Collect data every second
#
#     replay_thread = Thread(target=replay_packets)
#     replay_thread.start()
#
#     collect_data(80, attack_launched=False)
#
#     # Start attack in a separate thread
#     attack_thread = Thread(target=lambda: subprocess.run(['python', attack_script]))
#     attack_thread.start()
#
#     # Continue collecting data during attack
#     collect_data(80, attack_launched=True)
#
#     # Make sure all threads are finished
#     replay_thread.join()
#     attack_thread.join()
#
#
# # Output file for data collection
# output_file = 'combined_traffic_data.csv'
#
# for i in range(1, 5):
#     pcap_file = f'univ_pt{i}.pcap'
#     attack_script = 'attack_sim1.py'  # Change the script name for different attack parameters
#     print(f"Running simulation with {pcap_file} as background traffic and {attack_script} for attack traffic.")
#     replay_and_collect(pcap_file, attack_script, output_file)

import time
import subprocess
import pandas as pd
from scapy.all import rdpcap, sendp
from threading import Thread
import numpy as np
from scipy.stats import iqr, skew, kurtosis

# Constants
INTERFACE = 's1-eth1'
SWITCH = 's1'
NORMAL_TRAFFIC_FILE = 'univ1_pt1.pcap'
ATTACK_SCRIPT = 'attack_sim1.py'
OUTPUT_FILE = 'training_data_set.csv'
ATTACK_START = 80
TOTAL_DURATION = 160
SAMPLING_INTERVAL = 1


def collect_flow_entries(switch_id):
    command = f"sudo ovs-ofctl dump-flows {switch_id}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout


def parse_flow_entries(raw_data):
    entries = []
    lines = raw_data.strip().split('\n')[1:]
    for line in lines:
        if line.strip():  # empty lines
            fields = {
                'duration': float(line.split('duration=')[1].split(',')[0].strip('s')),
                'CP': int(line.split('n_packets=')[1].split(',')[0]),
                'CB': int(line.split('n_bytes=')[1].split(',')[0]),
            }
            entries.append(fields)
    return entries


def calculate_statistical_features(entries):
    tnfe = len(entries)
    features = {}
    for rule in entries:
        duration = rule['duration']
        cp = rule['CP']
        # cb = rule['CB']

        apits = duration if cp == 0 else duration / cp
        # aps = 0 if cp == 0 else cb / cp
        features = {
            'tnfe': tnfe,
            'APIT_mean': np.mean(apits) if apits else 0,
            'APIT_std': np.std(apits, ddof=1) if apits else 0,
            'APIT_iqr': iqr(apits) if apits else 0,
            'APIT_skewness': skew(apits) if apits else 0,
            'APIT_kurtosis': kurtosis(apits) if apits else 0,
            'cp_median': np.median(cp)
        }
    return features


# Function to collect data every second and append to CSV with features
def collect_and_save_data(label, duration, switch):
    start_time = time.time()
    while time.time() - start_time < duration:
        raw_data = collect_flow_entries(switch)
        entries = parse_flow_entries(raw_data)
        features = calculate_statistical_features(entries)
        features['timestamp'] = time.time()
        features['label'] = label

        df = pd.DataFrame([features])
        with open(OUTPUT_FILE, 'a') as f:
            df.to_csv(f, header=f.tell() == 0, index=False)

        time.sleep(SAMPLING_INTERVAL)


# Function to handle replay and attack simulation
def replay_traffic_and_simulate_attack():
    replay_thread = Thread(target=replay_traffic, args=(NORMAL_TRAFFIC_FILE, INTERFACE))
    replay_thread.start()
    collect_and_save_data(0, ATTACK_START, SWITCH)

    # Start the attack script
    attack_process = subprocess.Popen(['sudo python3 ', ATTACK_SCRIPT])
    collect_and_save_data(1, TOTAL_DURATION - ATTACK_START, SWITCH)

    replay_thread.join()
    attack_process.terminate()


def replay_traffic(pcap_file, iface):
    packets = rdpcap(pcap_file)
    sendp(packets, iface=iface, verbose=False)


if __name__ == '__main__':
    replay_traffic_and_simulate_attack()
