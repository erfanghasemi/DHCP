import dhcppython.packet as dhcpp
import dhcppython.options as dhcpo
import socket
import ipaddress
import json
import utils
import threading
from time import sleep
from sys import maxsize

PORT = 2067
IP_ADDRESS = "0.0.0.0"
bufferSize = 1024
mac_ip_usedPair = {}
ip_lease_usedPair = {}
clients_info = []
time = 0

class myTimer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        while True:
            global time
            sleep(1)
            time += 1

class ipChecker(threading.Thread):
    def __init__(self, lease_time):
        threading.Thread.__init__(self)
        self.lease_time = lease_time

    def run(self):
        global time
        global mac_ip_usedPair
        global ip_lease_usedPair
        while True:
            utils.remove_client(ip_lease_usedPair, mac_ip_usedPair, clients_info, self.lease_time, time)                    

class clientRepresentation(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        while True:
            global time
            command = input()
            if command == "show clients":
                for client in clients_info:
                    print(f"Computer name: {client[0]}  -  MAC Address: {client[1]}  -  IP Address: {client[2]}  -  Expire Time: {client[3]-(time-client[4])}")
                print("-----------------------------------------------------------------------------------------------------------------")

def DHCPAck(socket, DHCPRequest: dhcpp.DHCPPacket, selected_ip: str, lease_time: int):
    global time
    mac_ip_usedPair[DHCPRequest.chaddr] = selected_ip
    device_name = DHCPRequest.options[0].data.decode("utf-8")
  
    if selected_ip in ip_lease_usedPair:
        for client in clients_info:
            if client[1] == DHCPRequest.chaddr:
                client[4] = time
    else:
        clients_info.append(list([device_name, DHCPRequest.chaddr, selected_ip, lease_time, time]))

    ip_lease_usedPair[selected_ip] = time

    pkt = dhcpp.DHCPPacket(op="BOOTREPLY", htype="ETHERNET", hlen=6, hops=0, xid=DHCPRequest.xid, secs=0, flags=32768, ciaddr=ipaddress.IPv4Address('0.0.0.0'), yiaddr=ipaddress.IPv4Address(mac_ip_usedPair[DHCPRequest.chaddr]), siaddr=ipaddress.IPv4Address('0.0.0.0'), giaddr=ipaddress.IPv4Address('0.0.0.0'), chaddr=DHCPRequest.chaddr, sname=b'', file=b'', options=dhcpo.OptionList([dhcpo.MessageType(code=53, length=1, data=b'\x05'),  dhcpo.End(code=255, length=0, data=b'')]))
    socket.sendto(pkt.asbytes, ('<broadcast>', 2068))
    

def DHCPOffer(socket, DHCPDiscover: dhcpp.DHCPPacket, ip_pool: list, block_MACs: list):
    if DHCPDiscover.chaddr in block_MACs:
        return -1

    selected_ip = utils.get_ip(ip_pool, mac_ip_usedPair, DHCPDiscover.chaddr)
    pkt = dhcpp.DHCPPacket(op="BOOTREPLY", htype="ETHERNET", hlen=6, hops=0, xid=DHCPDiscover.xid, secs=0, flags=32768, ciaddr=ipaddress.IPv4Address('0.0.0.0'), yiaddr=ipaddress.IPv4Address(selected_ip), siaddr=ipaddress.IPv4Address('0.0.0.0'), giaddr=ipaddress.IPv4Address('0.0.0.0'), chaddr=DHCPDiscover.chaddr, sname=b'', file=b'', options=dhcpo.OptionList([dhcpo.MessageType(code=53, length=1, data=b'\x02'), dhcpo.options.short_value_to_object(51, lease_time), dhcpo.End(code=255, length=0, data=b'')]))
    socket.sendto(pkt.asbytes, ('<broadcast>', 2068))
    return selected_ip

def recv_DHCPDiscover(socket):
    discover = socket.recvfrom(bufferSize)[0]
    discover = dhcpp.DHCPPacket.from_bytes(discover)
    return discover

def recv_DHCPRequest(socket):
    request = socket.recvfrom(bufferSize)[0]
    request = dhcpp.DHCPPacket.from_bytes(request)
    return request

def read_information():

    with open("configs.json", 'r') as config:
        info = json.load(config)

        lease_time = info['lease_time']
        block_MACs = info['block_list']

        pool_mode = info['pool_mode']
        if pool_mode == "range":
            start = info['range']['from']
            stop = info['range']['to']
            ip_pool = utils.create_IP_range(start, stop, pool_mode)

        elif pool_mode == "subnet":
            ip_block = info['subnet']['ip_block']
            subnet_mask = info['subnet']['subnet_mask']
            ip_pool = utils.create_IP_range(ip_block, subnet_mask, pool_mode)

        for mac_address in info['reservation_list']:
            mac_ip_usedPair[mac_address] = info['reservation_list'][mac_address]
            clients_info.append(["Static IP", mac_address, info['reservation_list'][mac_address], maxsize, 0])
        
        # print(used_ip)
        # print(f"Pool Mode: {pool_mode}")
        # print(f"block MACs: {block_MACs}")
        # print(f"lease time :{lease_time}")
        # for ip in ip_pool:
        #     print(ip)
        return lease_time, block_MACs, ip_pool

if __name__ == "__main__":
      
    UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    UDPServerSocket.bind((IP_ADDRESS, PORT))
    print(f"Server is listening on {IP_ADDRESS}:{PORT}")
    
    lease_time, block_MACs, ip_pool = read_information()
    timer= myTimer()
    show_clients = clientRepresentation()
    ip_checker = ipChecker(lease_time)

    timer.start()
    show_clients.start()
    ip_checker.start()
    
    while True:
        discover = recv_DHCPDiscover(UDPServerSocket)
        selected_ip = DHCPOffer(UDPServerSocket, discover, ip_pool, block_MACs)
        request = recv_DHCPRequest(UDPServerSocket)
        DHCPAck(UDPServerSocket, request, selected_ip, lease_time)
        

