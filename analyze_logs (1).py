import os
import re
import math
import numpy as np
import matplotlib.pyplot as plt

# ---------- 解析函数 ----------

def parse_iperf_throughput(filepath):
    """
    解析 iperf (TCP/UDP) 日志中的平均吞吐量 (Mbits/sec).
    支持 Kbits/sec, Mbits/sec, Gbits/sec，并统一换算到 Mbits/sec.
    """
    if not os.path.exists(filepath):
        print(f"[WARN] File not found: {filepath}")
        return math.nan

    throughput = math.nan
    with open(filepath, 'r') as f:
        for line in f:
            if "bits/sec" in line:
                # 匹配 3.36 Mbits/sec / 19.3 Gbits/sec / 512 Kbits/sec 等
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
    """
    从一行 iperf 输出中解析带单位的速率，返回 Mbits/sec.
    支持 Kbits/sec, Mbits/sec, Gbits/sec.
    """
    m = re.search(r'([\d\.]+)\s+([KMG])bits/sec', line)
    if not m:
        # 兜底：只有 bits/sec 没有前缀
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
    """
    解析 UDP iperf 日志：
    返回 (throughput_Mbps, jitter_ms, loss_pct).
    尽量从最后几行带 bits/sec 的行中提取，
    支持 K/M/Gbits/sec。
    """
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
            # 吞吐：只要有 bits/sec，就用统一的解析函数
            val = _parse_bits_per_sec(line)
            if not math.isnan(val):
                throughput = val

            # Jitter: 找该行中的 "xx ms"
            m_jit = re.search(r'([\d\.]+)\s*ms', line)
            if m_jit:
                try:
                    jitter = float(m_jit.group(1))
                except ValueError:
                    pass

            # UDP 丢包率 X/Y (Z%)
            m_loss = re.search(r'(\d+)/(\d+)\s*\(([\d\.]+)%\)', line)
            if m_loss:
                loss_pct = float(m_loss.group(3))

    # 如果只有 throughput 成功解析，jitter/loss 没有，也可以接受，只是会在图上留空
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

        # 解析 packet loss（如果有 summary）
        if "packet loss" in line:
            # e.g. "20 packets transmitted, 20 received, 0% packet loss, time 19451ms"
            m_loss = re.search(r'(\d+)%\s+packet loss', line)
            if m_loss:
                loss_pct = float(m_loss.group(1))

        # 解析 rtt summary（如果有）
        if "rtt " in line or "round-trip" in line:
            # e.g. "rtt min/avg/max/mdev = 0.032/0.043/0.050/0.003 ms"
            m_rtt = re.search(r'=\s*[\d\.]+/([\d\.]+)/[\d\.]+/[\d\.]+\s*ms', line)
            if m_rtt:
                avg_rtt = float(m_rtt.group(1))

    # 如果 summary 里没有 avg_rtt，但有很多 time=，就用 time= 的平均值
    if math.isnan(avg_rtt) and len(rtts) > 0:
        avg_rtt = sum(rtts) / len(rtts)

    # 如果没有 packet loss 信息，但有 rtts（说明收到了一些包），默认为 0%
    if math.isnan(loss_pct) and len(rtts) > 0:
        loss_pct = 0.0

    if math.isnan(avg_rtt) or math.isnan(loss_pct):
        print(f"[WARN] Ping metrics incomplete in {filepath}")

    return avg_rtt, loss_pct


# ---------- 收集三组实验的所有指标 ----------

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

# ---------- 画图帮助函数 ----------

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


# ---------- 生成四张图 ----------

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
