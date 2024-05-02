from minmaxScaler import MinMaxScaler
from lcrn_model import create_lrcn_model
import re
import subprocess
import numpy as np
from attack_detection import detect_sfto_attack

scaler = MinMaxScaler()
lrcn_model = create_lrcn_model((5, 1), 3, 3, 1)


def collect_flow_entries(sampling_interval, switch_id):
    command = f"sudo ovs-ofctl dump-flows {switch_id}"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    flow_entries = parse_flow_entries(output.decode('utf-8'))
    return flow_entries


def parse_flow_entries(flow_entries):
    cp_pattern = re.compile(r'n_packets=(\d+)')
    cb_pattern = re.compile(r'n_bytes=(\d+)')
    duration_pattern = re.compile(r'duration=([\d.]+)')
    flow_entries_lines = flow_entries.strip().split('\n')[1:]

    flow_data = []
    for entry in flow_entries_lines:
        cp_match = cp_pattern.search(entry)
        cb_match = cb_pattern.search(entry)
        duration_match = duration_pattern.search(entry)

        cp = int(cp_match.group(1)) if cp_match else 0
        cb = int(cb_match.group(1)) if cb_match else 0
        duration = float(duration_match.group(1)) if duration_match else 0.000

        flow_data.append({'CP': cp, 'CB': cb, 'duration': duration})

    return flow_data


def poll_sdn_switch():
    # flow_count = len(collect_flow_entries(1, "s1"))
    flow_data = collect_flow_entries(1, "s1")
    return flow_data


def main():
    Size_window = 5  # The size of the window for prediction
    TH = 0.75  # Threshold for the rule number
    size_flowtable = 3500  # Size of the flow table
    Window = []

    while True:
        flowtable_data = {}
        flowtable_data = poll_sdn_switch()
        Num_rule = len(flowtable_data)
        Window.append(Num_rule)

        if len(Window) >= Size_window:
            Window_array = np.array(Window[-Size_window:]).reshape(-1, 1)
            Window_normalized = scaler.transform(Window_array)
            prediction_normalized = lrcn_model.predict(Window_normalized.reshape(1, Size_window, 1))
            fn1, fn2 = scaler.inverse_transform(prediction_normalized.flatten())[0]
            Window.pop(0)

        if fn2 > TH * size_flowtable:
            detect_sfto_attack(flowtable_data)
            break
        if len(Window) > 10:
            break
    return fn1, fn2


if __name__ == "__main__":
    main()
