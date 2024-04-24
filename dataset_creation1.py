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
        flow_dump = collect_flow_data(switch)
        flow_entries = parse_flow_entries(flow_dump)

        cps = np.array([entry['n_packets'] for entry in flow_entries])
        cbs = np.array([entry['n_bytes'] for entry in flow_entries])
        durations = np.array([entry['duration'] for entry in flow_entries])
        apits = durations / cps
        aps = cbs / cps

        apit = durations if cps == 0 else durations / cps
        aps = 0 if cps == 0 else cbs / cps
        df = pd.DataFrame({
            'APIT': apit,
            'APS': aps,
            'CP': cps,
            'CB': cps,
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
