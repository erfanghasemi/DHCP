import dhcppython.packet as dhcpp
import dhcppython.options as dhcpo
import socket
import ipaddress
import json
import utils
import threading
from time import perf_counter, sleep
from sys import maxsize

PORT = 2067
IP_ADDRESS = "0.0.0.0"
bufferSize = 1024
mac_ip_usedPair = {}
ip_lease_usedPair = {}
clients_info = []
received_msg = None
received_msg_flag = 0
time = 0


class myTimer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        while True:
            global time
            sleep(1)
            time += 1

class Receiver(threading.Thread):
    def __init__(self, socket):
        threading.Thread.__init__(self)
        self.socket = socket

    def run(self):
        global received_msg, received_msg_flag
        while True:
            received_msg = self.socket.recvfrom(bufferSize)[0]
            received_msg = dhcpp.DHCPPacket.from_bytes(received_msg)
            received_msg_flag = 1


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

class testACKResend(threading.Thread):
    def __init__(self, UDPServerSocket, received_msg, selected_ip, lease_time):
        threading.Thread.__init__(self)
        self.UDPServerSocket = UDPServerSocket
        self.received_msg = received_msg
        self.selected_ip = selected_ip
        self.lease_time = lease_time

    def run(self):
        sleep(15)
        DHCPAck(self.UDPServerSocket, self.received_msg, self.selected_ip, self.lease_time)
        print(f"The server sent Ack message to client with IP Address: {selected_ip} and Lease-time: {lease_time}")

def DHCPAck(socket, DHCPRequest: dhcpp.DHCPPacket, selected_ip: str, lease_time: int):
    sleep(0.25)
    global time
    mac_ip_usedPair[DHCPRequest.chaddr] = selected_ip
    device_name = DHCPRequest.options[1].data.decode("utf-8")
  
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
    sleep(0.25)
    if DHCPDiscover.chaddr in block_MACs:
        print("This MAC Address has been blocked")
        return -1

    selected_ip = utils.get_ip(ip_pool, mac_ip_usedPair, DHCPDiscover.chaddr)
    pkt = dhcpp.DHCPPacket(op="BOOTREPLY", htype="ETHERNET", hlen=6, hops=0, xid=DHCPDiscover.xid, secs=0, flags=32768, ciaddr=ipaddress.IPv4Address('0.0.0.0'), yiaddr=ipaddress.IPv4Address(selected_ip), siaddr=ipaddress.IPv4Address('0.0.0.0'), giaddr=ipaddress.IPv4Address('0.0.0.0'), chaddr=DHCPDiscover.chaddr, sname=b'', file=b'', options=dhcpo.OptionList([dhcpo.MessageType(code=53, length=1, data=b'\x02'), dhcpo.options.short_value_to_object(51, lease_time), dhcpo.End(code=255, length=0, data=b'')]))
    socket.sendto(pkt.asbytes, ('<broadcast>', 2068))
    return selected_ip

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
    UDPServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    UDPServerSocket.bind((IP_ADDRESS, PORT))
    print(f"Server is listening on {IP_ADDRESS}:{PORT}\n")
    
    lease_time, block_MACs, ip_pool = read_information()
    timer= myTimer()
    show_clients = clientRepresentation()
    ip_checker = ipChecker(lease_time)
    receiver = Receiver(UDPServerSocket)

    timer.start()
    show_clients.start()
    ip_checker.start()
    receiver.start()

    while True:
        if received_msg_flag == 1:
            received_msg_flag = 0
            type_msg = int.from_bytes(received_msg.options.by_code(53).data, "big")

            if type_msg == 1:
                # print("The server receive a Discover message from client")
                selected_ip = DHCPOffer(UDPServerSocket, received_msg, ip_pool, block_MACs)
                # print(f"The server sent Offer message to client with IP Address: {selected_ip} and Lease-time: {lease_time}")
            elif type_msg == 3:
                # print("The server receive a Request message from client")
                DHCPAck(UDPServerSocket, received_msg, selected_ip, lease_time)
                # print(f"The server sent Ack message to client with IP Address: {selected_ip} and Lease-time: {lease_time}")
                
                ################### This section for test Ack resend ###################
                # ack_test_resend = testACKResend(UDPServerSocket, received_msg, selected_ip, lease_time)
                # ack_test_resend.start()
                ########################################################################
                
            

        

