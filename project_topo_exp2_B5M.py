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


def run_experiment_2(net):
    """
    Experiment 2 (high-load / congested):
    - Main measured flow: h2 -> h1
    - Background flows to create congestion: h4 -> h3, h6 -> h5
    - 对 TCP / UDP: throughput 来自 iperf，RTT / loss 来自并发 ping
    """
    h1, h2, h3, h4, h5, h6 = net.get('h1', 'h2', 'h3', 'h4', 'h5', 'h6')

    server_ip = h1.IP()
    bkg1_ip = h3.IP()
    bkg2_ip = h5.IP()
    print(f"\n[Info] h1 IP = {server_ip}, h3 IP = {bkg1_ip}, h5 IP = {bkg2_ip}")

    def kill_all():
        "Kill any leftover iperf/ping in these hosts."
        for h in [h1, h2, h3, h4, h5, h6]:
            h.cmd('pkill iperf')
            h.cmd('pkill ping')

    # ========================
    # 1) TCP under high load + concurrent ping
    # ========================
    print("\n=== Experiment 2 (High-load): TCP h2 -> h1 with background traffic + ping ===")
    kill_all()

    # Start TCP servers
    h1.cmd('iperf -s &')   # main flow server
    h3.cmd('iperf -s &')   # background server 1
    h5.cmd('iperf -s &')   # background server 2

    # Start background TCP clients (longer duration, high load)
    # h4 -> h3, h6 -> h5
    h4.cmd(f'iperf -c {bkg1_ip} -t 20 &')
    h6.cmd(f'iperf -c {bkg2_ip} -t 20 &')

    # Start ping concurrently from h2 to h1 (RTT/loss during TCP flow)
    h2.cmd(f'ping -i 0.2 -c 50 {server_ip} > exp2_ping_during_tcp_h2_h1.log &')

    # Main TCP measurement (h2 -> h1)
    tcp_output = h2.cmd(f'iperf -c {server_ip} -t 10')

    kill_all()

    print("--- TCP raw output (exp2) ---")
    print(tcp_output)
    with open('exp2_tcp_h2_h1.log', 'w') as f:
        f.write(tcp_output)
    print("Saved TCP log to exp2_tcp_h2_h1.log")
    print("Saved ping-during-TCP log to exp2_ping_during_tcp_h2_h1.log")

    # ========================
    # 2) UDP under high load + concurrent ping
    # ========================
    print("\n=== Experiment 2 (High-load): UDP h2 -> h1 with background traffic + ping ===")
    kill_all()

    # Start UDP servers
    h1.cmd('iperf -s -u &')
    h3.cmd('iperf -s -u &')
    h5.cmd('iperf -s -u &')

    # Background UDP clients with higher rate
    h4.cmd(f'iperf -c {bkg1_ip} -u -b 10M -t 20 &')
    h6.cmd(f'iperf -c {bkg2_ip} -u -b 10M -t 20 &')

    # Ping during UDP flow0
    h2.cmd(f'ping -i 0.2 -c 50 {server_ip} > exp2_ping_during_udp_h2_h1.log &')

    # Main UDP measurement (h2 -> h1)
    udp_output = h2.cmd(f'iperf -c {server_ip} -u -b 5M -t 10')

    kill_all()

    print("--- UDP raw output (exp2) ---")
    print(udp_output)
    with open('exp2_udp_h2_h1.log', 'w') as f:
        f.write(udp_output)
    print("Saved UDP log to exp2_udp_h2_h1.log")
    print("Saved ping-during-UDP log to exp2_ping_during_udp_h2_h1.log")

    # ==============================
    # 3) ICMP ping-only under high load
    # ==============================
    print("\n=== Experiment 2 (High-load): ICMP ping-only h2 -> h1 with background traffic ===")
    kill_all()

    # Use background UDP flows to create load while we only ping
    h3.cmd('iperf -s -u &')
    h5.cmd('iperf -s -u &')
    h4.cmd(f'iperf -c {bkg1_ip} -u -b 10M -t 20 &')
    h6.cmd(f'iperf -c {bkg2_ip} -u -b 10M -t 20 &')

    # Ping under high load (no main iperf from h2)
    ping_output = h2.cmd(f'ping -c 20 {server_ip}')

    kill_all()

    print("--- Ping-only raw output (exp2) ---")
    print(ping_output)
    with open('exp2_ping_h2_h1.log', 'w') as f:
        f.write(ping_output)
    print("Saved ping-only-under-load log to exp2_ping_h2_h1.log")


def main():
    net = None
    try:
        net = create_network()
        # Optional sanity check
        print("\n*** Quick pingall (optional sanity check)")
        net.pingAll()

        # Run high-load / congested experiment
        run_experiment_2(net)

        print("\n*** Entering Mininet CLI (you can inspect hosts/logs)")
        CLI(net)
    finally:
        if net is not None:
            net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    main()

