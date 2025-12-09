from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel

def create_network():
    "Create the 20-host, 5-switch topology (standalone switches)."
    net = Mininet(controller=None, link=TCLink, switch=OVSSwitch)

    print("*** Creating switches (standalone mode)")
    s1 = net.addSwitch('s1', failMode='standalone')
    s2 = net.addSwitch('s2', failMode='standalone')
    s3 = net.addSwitch('s3', failMode='standalone')
    s4 = net.addSwitch('s4', failMode='standalone')
    s5 = net.addSwitch('s5', failMode='standalone')

    print("*** Creating hosts")
    h1 = net.addHost('h1')
    h2 = net.addHost('h2')
    h3 = net.addHost('h3')
    h4 = net.addHost('h4')
    h5 = net.addHost('h5')
    h6 = net.addHost('h6')
    h7 = net.addHost('h7')
    h8 = net.addHost('h8')
    h9 = net.addHost('h9')
    h10 = net.addHost('h10')
    h11 = net.addHost('h11')
    h12 = net.addHost('h12')
    h13 = net.addHost('h13')
    h14 = net.addHost('h14')
    h15 = net.addHost('h15')
    h16 = net.addHost('h16')
    h17 = net.addHost('h17')
    h18 = net.addHost('h18')
    h19 = net.addHost('h19')
    h20 = net.addHost('h20')

    print("*** Creating links host<->switch")
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(h3, s1)
    net.addLink(h4, s1)

    net.addLink(h5, s2)
    net.addLink(h6, s2)
    net.addLink(h7, s2)
    net.addLink(h8, s2)

    net.addLink(h9, s3)
    net.addLink(h10, s3)
    net.addLink(h11, s3)
    net.addLink(h12, s3)

    net.addLink(h13, s4)
    net.addLink(h14, s4)
    net.addLink(h15, s4)
    net.addLink(h16, s4)

    net.addLink(h17, s5)
    net.addLink(h18, s5)
    net.addLink(h19, s5)
    net.addLink(h20, s5)

    print("*** Creating links between switches")
    net.addLink(s1, s4)
    net.addLink(s3, s5)
    net.addLink(s1, s2)
    net.addLink(s2, s3)

    print("*** Starting network")
    net.start()
    return net

def run_experiment_1(net):
    "Experiment 1 (baseline): TCP, UDP, ICMP between h2 and h1."
    h1 = net.get('h1')
    h2 = net.get('h2')

    server_ip = h1.IP()
    print(f"\n[Info] h1 IP address = {server_ip}")

    # Helper: kill any old iperf
    h1.cmd('pkill iperf')
    h2.cmd('pkill iperf')

    # ===== TCP + ping (RTT/loss during TCP flow) =====
    print("\n=== Experiment 1: TCP h2 -> h1 (with concurrent ping) ===")
    h1.cmd('iperf -s &')

    # 在 h2 上后台启动 ping，同时测 RTT / packet loss
    h2.cmd(f'ping -i 0.2 -c 50 {server_ip} > exp1_ping_during_tcp_h2_h1.log &')

    # 这时再跑 TCP iperf
    tcp_output = h2.cmd(f'iperf -c {server_ip} -t 10')
    h1.cmd('pkill iperf')
    h2.cmd('pkill ping')

    print("--- TCP raw output (exp1) ---")
    print(tcp_output)
    with open('exp1_tcp_h2_h1.log', 'w') as f:
        f.write(tcp_output)
    print("Saved TCP log to exp1_tcp_h2_h1.log")
    print("Saved ping-during-TCP log to exp1_ping_during_tcp_h2_h1.log")

    # ===== UDP + ping (RTT/loss during UDP flow) =====
    print("\n=== Experiment 1: UDP h2 -> h1 (with concurrent ping) ===")
    h1.cmd('pkill iperf')
    h2.cmd('pkill iperf')
    h1.cmd('iperf -s -u &')

    # UDP 流期间的 ping
    h2.cmd(f'ping -i 0.2 -c 50 {server_ip} > exp1_ping_during_udp_h2_h1.log &')
    udp_output = h2.cmd(f'iperf -c {server_ip} -u -b 500M -t 10')
    h1.cmd('pkill iperf')
    h2.cmd('pkill ping')

    print(udp_output)
    with open('exp1_udp_h2_h1.log', 'w') as f:
        f.write(udp_output)
    print("Saved UDP log to exp1_udp_h2_h1.log")
    print("Saved ping-during-UDP log to exp1_ping_during_udp_h2_h1.log")

    # ===== 纯 ICMP baseline（无额外流量） =====
    print("\n=== Experiment 1: ICMP ping-only h2 -> h1 (no extra traffic) ===")
    ping_output = h2.cmd(f'ping -c 20 {server_ip}')
    print("--- Ping-only raw output (exp1) ---")
    print(ping_output)
    with open('exp1_ping_h2_h1.log', 'w') as f:
        f.write(ping_output)
    print("Saved ping-only log to exp1_ping_h2_h1.log")


def main():
    net = None
    try:
        net = create_network()
        # Optional: quick connectivity sanity check
        print("\n*** Quick pingall (optional sanity check)")
        net.pingAll()

        # Run your baseline measurements
        run_experiment_1(net)

        print("\n*** Entering Mininet CLI (you can inspect hosts/logs)")
        CLI(net)
    finally:
        if net is not None:
            net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    main()
