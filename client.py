import dhcppython.packet as dhcp
import socket
from uuid import getnode

# all times value in seconds
ack_timeout = 20   
backoff_cutoff = 120
initial_interval = 10
bufferSize = 1024

PORT = 2068

BROADCAST = ('<broadcast>', 2067)

def DHCPDiscover(socket: socket, mac_address: str):
    packet = dhcp.DHCPPacket.Discover(mac_address)
    socket.sendto(packet.asbytes, BROADCAST)

# def DHCPRequest(socket: socket, mac_address: str, DHCPOffer: dhcp.DHCPPacket):
#     packet = dhcp.DHCPPacket.Request(mac_address, 0, DHCPOffer.xid)
#     socket.sendto(packet.asbytes, BROADCAST)

def recv_DHCPOffer(socket, mac_address):
    offer = UDPClientSocket.recvfrom(bufferSize)
    offer = dhcp.DHCPPacket.from_bytes(offer)
    


def recv_DHCPAck(socket, mac_address):
    pass



if __name__ == "__main__":
    
    UDPClientSocket = socket.socket( socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    UDPClientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    mac_address = ':'.join(['{:02x}'.format((getnode() >> ele) & 0xff)for ele in range(0,8*6,8)][::-1])
    
    
    DHCPDiscover(UDPClientSocket, mac_address)
    
    print("Client run Properly!")