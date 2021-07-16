import ipaddress
import dhcppython.packet as dhcpp
import dhcppython.options as dhcpo
import socket
from uuid import getnode
import threading
from time import sleep

# all times value in seconds
ack_timeout = 20   
backoff_cutoff = 120
initial_interval = 10
bufferSize = 1024

PORT = 2068
IP_ADDRESS = "0.0.0.0"
BROADCAST = ('<broadcast>', 2067)

time = 0

class myTimer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        while True:
            global time
            sleep(1)
            time += 1


def DHCPDiscover(socket: socket, mac_address: str):
    packet = dhcpp.DHCPPacket.Discover(mac_address)
    socket.sendto(packet.asbytes, BROADCAST)

def DHCPRequest(socket: socket, DHCPOffer: dhcpp.DHCPPacket):
    packet = dhcpp.DHCPPacket(op="BOOTREQUEST", htype="ETHERNET", hlen=6, hops=0, xid=DHCPOffer.xid, secs=0, flags=32768, ciaddr=ipaddress.IPv4Address('0.0.0.0'), yiaddr=ipaddress.IPv4Address('0.0.0.0'), siaddr=ipaddress.IPv4Address('0.0.0.0'), giaddr=ipaddress.IPv4Address('0.0.0.0'), chaddr=DHCPOffer.chaddr, sname=b'', file=b'', options=dhcpo.OptionList([dhcpo.options.short_value_to_object(12, "Erfan_Laptop"), dhcpo.MessageType(code=53, length=1, data=b'\x03'),  dhcpo.End(code=255, length=0, data=b'')]))
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
    timer= myTimer()
    timer.start()

    mac_address = ':'.join(['{:02x}'.format((getnode() >> ele) & 0xff)for ele in range(0,8*6,8)][::-1])
    # mac_address = "00:0a:d2:a2:bc:46"


    DHCPDiscover(UDPClientSocket, mac_address)
    offer = recv_DHCPOffer(UDPClientSocket)
    lease_time = int.from_bytes(offer.options[1].data, "big")

    DHCPRequest(UDPClientSocket, offer)
    ack = recv_DHCPAck(UDPClientSocket)
    ip_address = ack.yiaddr
    print(f"IP Address: {ip_address}")

