import time
import subprocess
import pandas as pd
from scapy.all import rdpcap, sendp
import numpy as np
from threading import Thread

INTERFACE = 's1-eth1'
SWITCH = 's1'
BENIGN_TRAFFIC_FILE = 'univ1_pt1.pcap'
ATTACK_SCRIPT = 'attack_sim1.py'
OUTPUT_CSV_FILE = 'training_data.csv'
TRAFFIC_DURATION = 80  # Duration to send benign traffic and attack traffic
SAMPLING_INTERVAL = 1  # Interval for data collection

OVSCMD = "sudo ovs-ofctl dump-flows {switch}"

df_columns = ['APIT', 'APS', 'CP', 'CB', 'Label']
pd.DataFrame(columns=df_columns).to_csv(OUTPUT_CSV_FILE, index=False)


def collect_flow_data(switch):
    result = subprocess.run(OVSCMD.format(switch=switch), shell=True, capture_output=True, text=True)
    return result.stdout


def parse_flow_entries(raw_data):
    entries = []
    lines = raw_data.strip().split('\n')[1:]
    for line in lines:
        if line.strip():
            fields = {
                'duration': float(line.split('duration=')[1].split(',')[0].strip('s')),
                'CP': int(line.split('n_packets=')[1].split(',')[0]),
                'CB': int(line.split('n_bytes=')[1].split(',')[0]),
            }
            entries.append(fields)
    return entries


# def replay_traffic(pcap_file, iface, duration):
#     packets = rdpcap(pcap_file)
#     sendp(packets, iface=iface, verbose=False, inter=0.01, realtime=True)
def replay_traffic(pcap_file, iface):
    command = ['sudo', 'tcpreplay', '--intf1=' + iface, '--pps=', 1200, pcap_file]
    subprocess.run(command)


def simulate_attack(attack_script):
    subprocess.Popen(['python3', attack_script])


def collect_and_append_data(label, total_duration, switch, output_file):
    start_time = time.time()
    while time.time() - start_time < total_duration:
        raw_data = collect_flow_data(switch)
        entries = parse_flow_entries(raw_data)

        # Ensuring the entries are not empty
        if not entries:
            continue

        # Calculate features
        cps = np.array([entry['n_packets'] for entry in entries])
        cbs = np.array([entry['n_bytes'] for entry in entries])
        durations = np.array([entry['duration'] for entry in entries])

        # Avoid division by zero and ensuring there is more than one packet
        # apit = durations[1:] / cps[:-1] if cps.size > 1 else np.array([0])
        apit = np.where(cps > 0, durations / cps, durations)
        aps = cbs / cps if cps.size > 0 and not np.any(cps == 0) else np.array([0])

        # Creating DataFrame for this batch
        df = pd.DataFrame({
            'APIT': np.mean(apit) if apit.size > 0 else 0,
            'APS': np.mean(aps) if aps.size > 0 else 0,
            'CP': np.sum(cps) if cps.size > 0 else 0,
            'CB': np.sum(cbs) if cbs.size > 0 else 0,
            'Label': label
        }, index=[0])

        # Append batch DataFrame to CSV
        df.to_csv(output_file, mode='a', header=False, index=False)
        time.sleep(SAMPLING_INTERVAL)


# Run benign traffic and collect data
replay_thread = Thread(target=replay_traffic, args=(BENIGN_TRAFFIC_FILE, INTERFACE, TRAFFIC_DURATION))
replay_thread.start()
collect_and_append_data(0, TRAFFIC_DURATION, SWITCH, OUTPUT_CSV_FILE)

# Simulate attack and collect data
attack_thread = Thread(target=simulate_attack, args=(ATTACK_SCRIPT,))
attack_thread.start()
collect_and_append_data(1, TRAFFIC_DURATION, SWITCH, OUTPUT_CSV_FILE)

replay_thread.join()
attack_thread.join()
