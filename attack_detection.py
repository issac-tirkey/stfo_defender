import subprocess

import numpy as np
from scipy.stats import iqr, skew, kurtosis
from rule_number_predict import main
from lightgbm1 import lgb

fn1, fn2 = main()


def detect_sfto_attack(lightgbm_model, flowtable):
    features = []
    apit_data = []

    tnfe = len(flowtable)
    for rule in flowtable:
        duration = rule['duration']
        cp = rule['CP']
        cb = rule['CB']

        apit = duration if cp == 0 else duration / cp
        apit_data.append(apit)

        aps = 0 if cp == 0 else cb / cp
        cp_median = np.median(cp)

        # features.append(apit)
        # features.append(aps)
        features.append(cp_median)
        features.append(tnfe)
        rule_features = calculate_features(apit_data)
        features.extend(rule_features)

    prediction = lightgbm_model.predict(np.array([features]))

    dpred = prediction[0]
    result = 1 if dpred > 0.5 else 0

    if result == 1:
        Evict_rules(flowtable, dpred, cp, cb, apit, aps, fn1, tnfe)

    return dpred


def calculate_features(apit_info):
    apit_mean = np.mean(apit_info)
    apit_std = np.std(apit_info, ddof=1)
    apit_cv = apit_std / apit_mean if apit_mean else 0
    apit_iqr = iqr(apit_info)
    apit_skewness = skew(apit_info)
    apit_kurtosis = kurtosis(apit_info)

    rule_features = [apit_mean, apit_std, apit_cv, apit_iqr, apit_skewness, apit_kurtosis]
    return rule_features


lightgbm_model1 = lgb.Booster(model_file='mitigation_model.txt')


def Evict_rules(flowtable, dpred, cp, cb, apit, aps, fn1, size_flowtable):
    p = (len(flowtable) - threshold_TH) / size_flowtable
    p_e = p * dpred
    evict_list = []
    for rule in flowtable:
        score = lightgbm_model1.predict([[rule['CP'], rule['CB'], rule['APIT'], rule['APS']]])[0]
        rule['score'] = score
    flowtable.sort(key=lambda x: x['score'], reverse=True)

    cb_threshold = np.percentile([rule['CB'] for rule in flowtable], 90)
    apit_threshold = np.percentile([rule['APIT'] for rule in flowtable], 90)
    aps_threshold = np.percentile([rule['APS'] for rule in flowtable], 90)

    evict_list = [
        rule for rule in evict_list
        if rule['CB'] <= cb_threshold and rule['APIT'] <= apit_threshold and rule['APS'] <= aps_threshold
    ]
    for rule in evict_list:
        del_command = f"sudo ovs-ofctl del-flows {"s1"} ip,nw_src={rule['src_ip']},nw_dst={rule['dst_ip']},tp_src={rule['src_port']},tp_dst={rule['dst_port']},protocol={rule['protocol']}"
        subprocess.run(del_command, shell=True)

    return evict_list
