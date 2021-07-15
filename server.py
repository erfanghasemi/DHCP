import dhcppython.packet as dhcp
import socket
import ipaddress
import json
import utils

PORT = 2067
IP_ADDRESS = "0.0.0.0"
bufferSize = 1024
used_ip = {}


def DHCPAck(socket, mac_address):
    pass

def DHCPOffer(socket, DHCPDiscover: dhcp.DHCPPacket):
    packet = dhcp.DHCPPacket.Offer(DHCPDiscover.chaddr, 0, DHCPDiscover.xid, ipaddress.IPv4Address('192.168.56.4'))
    socket.sendto(packet.asbytes, '<broadcast>')

def recv_DHCPDiscover(socket):
    discover = socket.recvfrom(bufferSize)[0]
    discover = dhcp.DHCPPacket.from_bytes(discover)
    return discover

def recv_DHCPRequest(socket, mac_address):
    pass

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
            used_ip[mac_address] =info['reservation_list'][mac_address]
        
        # print(used_ip)
        # print(f"Pool Mode: {pool_mode}")
        # print(f"block MACs: {block_MACs}")
        # print(f"lease time :{lease_time}")
        # for ip in ip_pool:
        #     print(ip)

if __name__ == "__main__":

      
    UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    UDPServerSocket.bind((IP_ADDRESS, PORT))
    # print(f"Server is listening on {IP_ADDRESS}:{PORT}")
    
    read_information()  
    # while True:
    #     discover = recv_DHCPDiscover(UDPServerSocket)
        

