import dhcppython.packet as dhcpp
import dhcppython.options as dhcpo
import socket
import ipaddress
import json
import utils

PORT = 2067
IP_ADDRESS = "0.0.0.0"
bufferSize = 1024
used_ip = {}


def DHCPAck(socket, DHCPRequest: dhcpp.DHCPPacket):
    pkt = dhcpp.DHCPPacket(op="BOOTREPLY", htype="ETHERNET", hlen=6, hops=0, xid=DHCPRequest.xid, secs=0, flags=32768, ciaddr=ipaddress.IPv4Address('0.0.0.0'), yiaddr=ipaddress.IPv4Address(used_ip[DHCPRequest.chaddr]), siaddr=ipaddress.IPv4Address('0.0.0.0'), giaddr=ipaddress.IPv4Address('0.0.0.0'), chaddr=DHCPRequest.chaddr, sname=b'', file=b'', options=dhcpo.OptionList([dhcpo.MessageType(code=53, length=1, data=b'\x05'),  dhcpo.End(code=255, length=0, data=b'')]))
    socket.sendto(pkt.asbytes, ('<broadcast>', 2068))
    

def DHCPOffer(socket, DHCPDiscover: dhcpp.DHCPPacket, ip_pool: list, block_MACs: list):
    if DHCPDiscover.chaddr in block_MACs:
        return -1

    selected_ip = utils.get_ip(ip_pool, used_ip, DHCPDiscover.chaddr)
    # opt_list = dhcpo.OptionList(
    #     [
    #         dhcpo.options.short_value_to_object(51, lease_time),
    #         dhcpo.options.short_value_to_object(53, "DHCPOFFER")
    #     ]

    # )
    pkt = dhcpp.DHCPPacket(op="BOOTREPLY", htype="ETHERNET", hlen=6, hops=0, xid=DHCPDiscover.xid, secs=0, flags=32768, ciaddr=ipaddress.IPv4Address('0.0.0.0'), yiaddr=ipaddress.IPv4Address(selected_ip), siaddr=ipaddress.IPv4Address('0.0.0.0'), giaddr=ipaddress.IPv4Address('0.0.0.0'), chaddr=DHCPDiscover.chaddr, sname=b'', file=b'', options=dhcpo.OptionList([dhcpo.MessageType(code=53, length=1, data=b'\x02'), dhcpo.options.short_value_to_object(51, lease_time), dhcpo.End(code=255, length=0, data=b'')]))
    # pkt = dhcpp.DHCPPacket.Offer(DHCPDiscover.chaddr, seconds=0, tx_id=DHCPDiscover.xid, yiaddr=ipaddress.IPv4Address(selected_ip))
    socket.sendto(pkt.asbytes, ('<broadcast>', 2068))


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
            used_ip[mac_address] =info['reservation_list'][mac_address]
        
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
    while True:
        discover = recv_DHCPDiscover(UDPServerSocket)
        DHCPOffer(UDPServerSocket, discover, ip_pool, block_MACs)
        request = recv_DHCPRequest(UDPServerSocket)
        DHCPAck(UDPServerSocket, request)
        

