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
    # 统一带宽配置：10 Mbit/s
    linkopts = dict(bw=10)   # bw 单位是 Mbit/s
    
    print("*** Creating links host<->switch")
    net.addLink(h1, s1, **linkopts)
    net.addLink(h2, s1, **linkopts)
    net.addLink(h3, s1, **linkopts)
    net.addLink(h4, s1, **linkopts)

    net.addLink(h5, s2, **linkopts)
    net.addLink(h6, s2, **linkopts)
    net.addLink(h7, s2, **linkopts)
    net.addLink(h8, s2, **linkopts)

    net.addLink(h9, s3, **linkopts)
    net.addLink(h10, s3, **linkopts)
    net.addLink(h11, s3, **linkopts)
    net.addLink(h12, s3, **linkopts)

    net.addLink(h13, s4, **linkopts)
    net.addLink(h14, s4, **linkopts)
    net.addLink(h15, s4, **linkopts)
    net.addLink(h16, s4, **linkopts)

    net.addLink(h17, s5, **linkopts)
    net.addLink(h18, s5, **linkopts)
    net.addLink(h19, s5, **linkopts)
    net.addLink(h20, s5, **linkopts)

    print("*** Creating links between switches")
    net.addLink(s1, s4, **linkopts)
    net.addLink(s3, s5, **linkopts, delay='20ms')
    net.addLink(s1, s2, **linkopts, delay='20ms')
    net.addLink(s2, s3, **linkopts)

    print("*** Starting network")
    net.start()
    return net

def run_experiment_3(net):
    "Experiment 3 (delay topology): TCP, UDP, ICMP between h1 and h20."
    h1 = net.get('h1')
    h20 = net.get('h20')

    server_ip = h20.IP()
    print(f"\n[Info] h20 IP address = {server_ip}")

    # Helper: kill old iperf/ping
    h1.cmd('pkill iperf'); h1.cmd('pkill ping')
    h20.cmd('pkill iperf'); h20.cmd('pkill ping')

    # ===== TCP + ping (RTT/loss during TCP flow, under delay topology) =====
    print("\n=== Experiment 3 (delay): TCP h1 -> h20 (with concurrent ping) ===")
    h20.cmd('iperf -s &')   # server on h20
    h1.cmd(f'ping -i 0.2 -c 50 {server_ip} > exp3_ping_during_tcp_h1_h20.log &')

    # TCP client on h1
    tcp_output = h1.cmd(f'iperf -c {server_ip} -t 10')
    h20.cmd('pkill iperf')
    h1.cmd('pkill ping')

    print("--- TCP raw output (exp3) ---")
    print(tcp_output)
    with open('exp3_tcp_h1_h20.log', 'w') as f:
        f.write(tcp_output)
    print("Saved TCP log to exp3_tcp_h1_h20.log")
    print("Saved ping-during-TCP log to exp3_ping_during_tcp_h1_h20.log")

    # ===== UDP + ping (RTT/loss during UDP flow, under delay topology) =====
    print("\n=== Experiment 3 (delay): UDP h1 -> h20 (with concurrent ping) ===")
    h20.cmd('pkill iperf'); h1.cmd('pkill iperf'); h1.cmd('pkill ping')
    h20.cmd('iperf -s -u &')  # UDP server on h20

    h1.cmd(f'ping -i 0.2 -c 50 {server_ip} > exp3_ping_during_udp_h1_h20.log &')

    # 这里还是 5M，如果之后你统一想改大一点可以再调
    udp_output = h1.cmd(f'iperf -c {server_ip} -u -b 10M -t 10')
    h20.cmd('pkill iperf')
    h1.cmd('pkill ping')

    print("--- UDP raw output (exp3) ---")
    print(udp_output)
    with open('exp3_udp_h1_h20.log', 'w') as f:
        f.write(udp_output)
    print("Saved UDP log to exp3_udp_h1_h20.log")
    print("Saved ping-during-UDP log to exp3_ping_during_udp_h1_h20.log")

    # ===== 纯 ICMP baseline under delay topology =====
    print("\n=== Experiment 3 (delay): ICMP ping-only h1 -> h20 ===")
    ping_output = h1.cmd(f'ping -c 20 {server_ip}')
    print("--- Ping-only raw output (exp3) ---")
    print(ping_output)
    with open('exp3_ping_h1_h20.log', 'w') as f:
        f.write(ping_output)
    print("Saved ping-only log to exp3_ping_h1_h20.log")



def main():
    net = None
    try:
        net = create_network()
        # Optional: quick connectivity sanity check
        print("\n*** Quick pingall (optional sanity check)")
        net.pingAll()

        # Run your baseline measurements
        run_experiment_3(net)

        print("\n*** Entering Mininet CLI (you can inspect hosts/logs)")
        CLI(net)
    finally:
        if net is not None:
            net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    main()
