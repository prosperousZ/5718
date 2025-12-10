import os
import re
import math
import numpy as np
import matplotlib.pyplot as plt

def parse_iperf_throughput(filepath):

    if not os.path.exists(filepath):
        print(f"[WARN] File not found: {filepath}")
        return math.nan

    throughput = math.nan
    with open(filepath, 'r') as f:
        for line in f:
            if "bits/sec" in line:
        
                m = re.search(r'([\d\.]+)\s+([KMG])bits/sec', line)
                if m:
                    val = float(m.group(1))
                    unit = m.group(2)
                    if unit == 'K':
                        val = val / 1e3    # Kbits → Mbits
                    elif unit == 'M':
                        val = val          # Mbits → Mbits
                    elif unit == 'G':
                        val = val * 1e3    # Gbits → Mbits
                    throughput = val

    if math.isnan(throughput):
        print(f"[WARN] No throughput parsed from {filepath}")
    return throughput

def _parse_bits_per_sec(line):

    m = re.search(r'([\d\.]+)\s+([KMG])bits/sec', line)
    if not m:
     
        m2 = re.search(r'([\d\.]+)\s+bits/sec', line)
        if not m2:
            return math.nan
        val = float(m2.group(1))
        return val / 1e6  # bits/sec -> Mbits/sec
    val = float(m.group(1))
    unit = m.group(2)
    if unit == 'K':
        return val / 1e3
    elif unit == 'M':
        return val
    elif unit == 'G':
        return val * 1e3
    else:
        return math.nan
def parse_iperf_udp_metrics(filepath):

    if not os.path.exists(filepath):
        print(f"[WARN] File not found: {filepath}")
        return math.nan, math.nan, math.nan

    throughput = math.nan
    jitter = math.nan
    loss_pct = math.nan

    with open(filepath, 'r') as f:
        lines = f.readlines()

    for line in lines:
        if "bits/sec" in line:
       
            val = _parse_bits_per_sec(line)
            if not math.isnan(val):
                throughput = val

       
            m_jit = re.search(r'([\d\.]+)\s*ms', line)
            if m_jit:
                try:
                    jitter = float(m_jit.group(1))
                except ValueError:
                    pass

        
            m_loss = re.search(r'(\d+)/(\d+)\s*\(([\d\.]+)%\)', line)
            if m_loss:
                loss_pct = float(m_loss.group(3))


    if math.isnan(throughput) or math.isnan(jitter) or math.isnan(loss_pct):
        print(f"[WARN] UDP metrics incomplete in {filepath}")
    return throughput, jitter, loss_pct


def parse_ping_rtt_loss(filepath):
    """
    解析 ping 日志：
    - 优先使用 summary 的 'packet loss' 和 'rtt min/avg/max/mdev' 行；
    - 如果没有 summary（例如 ping 被 pkill 提前杀掉），
      则从每一行 'time=xxx ms' 直接计算平均 RTT，
      丢包率在没有明确信息时默认 0%。
    返回 (avg_rtt_ms, loss_pct).
    """
    if not os.path.exists(filepath):
        print(f"[WARN] File not found: {filepath}")
        return math.nan, math.nan

    avg_rtt = math.nan
    loss_pct = math.nan
    rtts = []  # 用于记录每个 icmp_seq 的 time

    with open(filepath, 'r') as f:
        lines = f.readlines()

    for line in lines:
        # 收集每一行的 time=... ms
        if " time=" in line:
            m_time = re.search(r'time=([\d\.]+)\s*ms', line)
            if m_time:
                try:
                    rtts.append(float(m_time.group(1)))
                except ValueError:
                    pass

     
        if "packet loss" in line:
            # e.g. "20 packets transmitted, 20 received, 0% packet loss, time 19451ms"
            m_loss = re.search(r'(\d+)%\s+packet loss', line)
            if m_loss:
                loss_pct = float(m_loss.group(1))


        if "rtt " in line or "round-trip" in line:
            # e.g. "rtt min/avg/max/mdev = 0.032/0.043/0.050/0.003 ms"
            m_rtt = re.search(r'=\s*[\d\.]+/([\d\.]+)/[\d\.]+/[\d\.]+\s*ms', line)
            if m_rtt:
                avg_rtt = float(m_rtt.group(1))


    if math.isnan(avg_rtt) and len(rtts) > 0:
        avg_rtt = sum(rtts) / len(rtts)


    if math.isnan(loss_pct) and len(rtts) > 0:
        loss_pct = 0.0

    if math.isnan(avg_rtt) or math.isnan(loss_pct):
        print(f"[WARN] Ping metrics incomplete in {filepath}")

    return avg_rtt, loss_pct




experiments = ["exp1", "exp2", "exp3"]
scenario_labels = ["Baseline (Exp1)", "High-load (Exp2)", "Delay (Exp3)"]
protocols = ["TCP", "UDP", "ICMP"]

# metrics[exp][protocol] = dict(...)
metrics = {exp: {p: {} for p in protocols} for exp in experiments}

for exp in experiments:
    # TCP
    tcp_log = f"{exp}_tcp_h1_h20.log"
    ping_tcp_log = f"{exp}_ping_during_tcp_h1_h20.log"

    tcp_thr = parse_iperf_throughput(tcp_log)
    tcp_rtt, tcp_loss = parse_ping_rtt_loss(ping_tcp_log)

    metrics[exp]["TCP"] = {
        "throughput_Mbps": tcp_thr,
        "rtt_ms": tcp_rtt,
        "loss_pct": tcp_loss,
        "jitter_ms": math.nan,  # jitter 对 TCP 没有定义
    }

    # UDP
    udp_log = f"{exp}_udp_h1_h20.log"
    ping_udp_log = f"{exp}_ping_during_udp_h1_h20.log"

    udp_thr, udp_jitter, udp_loss_udp = parse_iperf_udp_metrics(udp_log)
    udp_rtt, _udp_ping_loss = parse_ping_rtt_loss(ping_udp_log)
    # 根据 project 要求，UDP 的 packet loss 用 iperf 的统计
    metrics[exp]["UDP"] = {
        "throughput_Mbps": udp_thr,
        "rtt_ms": udp_rtt,
        "loss_pct": udp_loss_udp,
        "jitter_ms": udp_jitter,
    }

    # ICMP（只看 ping-only）
    ping_icmp_log = f"{exp}_ping_h1_h20.log"
    icmp_rtt, icmp_loss = parse_ping_rtt_loss(ping_icmp_log)

    metrics[exp]["ICMP"] = {
        "throughput_Mbps": math.nan,   # throughput 对纯 ICMP 不定义，这里留空
        "rtt_ms": icmp_rtt,
        "loss_pct": icmp_loss,
        "jitter_ms": math.nan,         # jitter 也不定义
    }

def plot_metric(metric_key, ylabel, title, filename):
    x = np.arange(len(experiments))  # 0,1,2

    plt.figure()
    for proto in protocols:
        y = [metrics[exp][proto][metric_key] for exp in experiments]
        # 使用 nan 的话，matplotlib 不会画出那些点
        plt.plot(x, y, marker='o', label=proto)

    plt.xticks(x, scenario_labels, rotation=15)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.4)
    plt.tight_layout()
    plt.savefig(filename)
    print(f"[INFO] Saved figure: {filename}")


plot_metric("throughput_Mbps",
            "Throughput (Mbits/sec)",
            "Throughput vs Scenario (TCP/UDP/ICMP)",
            "throughput_comparison.png")

plot_metric("rtt_ms",
            "Average RTT (ms)",
            "RTT vs Scenario (TCP/UDP/ICMP)",
            "rtt_comparison.png")

plot_metric("loss_pct",
            "Packet Loss (%)",
            "Packet Loss vs Scenario (TCP/UDP/ICMP)",
            "loss_comparison.png")

plot_metric("jitter_ms",
            "Jitter (ms)",
            "Jitter vs Scenario (TCP/UDP/ICMP)",
            "jitter_comparison.png")

plt.show()
