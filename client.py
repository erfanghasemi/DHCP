import ipaddress
import dhcppython.packet as dhcpp
import dhcppython.options as dhcpo
import socket
from uuid import getnode

# all times value in seconds
ack_timeout = 20   
backoff_cutoff = 120
initial_interval = 10
bufferSize = 1024

PORT = 2068
IP_ADDRESS = "0.0.0.0"

BROADCAST = ('<broadcast>', 2067)

def DHCPDiscover(socket: socket, mac_address: str):
    packet = dhcpp.DHCPPacket.Discover(mac_address)
    socket.sendto(packet.asbytes, BROADCAST)

def DHCPRequest(socket: socket, DHCPOffer: dhcpp.DHCPPacket):
    packet = dhcpp.DHCPPacket.Request(DHCPOffer.chaddr, 0, DHCPOffer.xid)
    socket.sendto(packet.asbytes, BROADCAST)

def recv_DHCPOffer(socket: socket):
    offer = socket.recvfrom(bufferSize)[0]
    offer = dhcpp.DHCPPacket.from_bytes(offer)
    return offer

def recv_DHCPAck(socket, ):
    ack = socket.recvfrom(bufferSize)[0]
    ack = dhcpp.DHCPPacket.from_bytes(ack)
    return ack



if __name__ == "__main__":
    
    UDPClientSocket = socket.socket( socket.AF_INET, socket.SOCK_DGRAM)
    UDPClientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    UDPClientSocket.bind((IP_ADDRESS, PORT))

    mac_address = ':'.join(['{:02x}'.format((getnode() >> ele) & 0xff)for ele in range(0,8*6,8)][::-1])
    
    DHCPDiscover(UDPClientSocket, mac_address)
    print("Send Discover message by client")
    offer = recv_DHCPOffer(UDPClientSocket)
    lease_time = int.from_bytes(offer.options[1].data, "big")
    ip_address = offer.yiaddr
    print(ip_address)
    DHCPRequest(UDPClientSocket, offer)
    ack = recv_DHCPAck(UDPClientSocket)


    print("Client run Properly!")