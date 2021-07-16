import ipaddress
from random import seed
from server import DHCPOffer
import dhcppython.packet as dhcpp
import dhcppython.options as dhcpo
import socket
from uuid import getnode
import threading
from time import sleep
from copy import deepcopy
import utils

# all times value in seconds
ack_timeout = 10
backoff_cutoff = 120
initial_interval = 10
bufferSize = 1024

ack_notfi = 0

PORT = 2068
IP_ADDRESS = "0.0.0.0"
BROADCAST = ('<broadcast>', 2067)

ip_address = None
set_time = 0
lease_time = 0

time = 0
received_msg = None
received_msg_flag = 0

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

class Dicovering(threading.Thread):
    def __init__(self, socket, mac_address):
        threading.Thread.__init__(self)
        self.socket = socket
        self.mac_address = mac_address

    def run(self):
        global received_msg, received_msg_flag, initial_interval, backoff_cutoff
        waiting_time = initial_interval
        while True:
            sleep(waiting_time)
            if ip_address is None:
                DHCPDiscover(self.socket, self.mac_address)
                print(f"The client sent Discover message after {waiting_time}")
                waiting_time = utils.discover_interval(waiting_time, initial_interval, backoff_cutoff)

class releaseIP(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global ip_address, set_time, lease_time
        while True:
            expire_time  = lease_time-(time-set_time)
            if expire_time <= 0:
                ip_address = None
                print("IP Address release!!")
                break


class keepIP(threading.Thread):
    def __init__(self, socket, DHCPOffer):
        threading.Thread.__init__(self)
        self.socket = socket
        self.DHCPOffer = DHCPOffer

    def run(self):
        global ip_address, set_time, lease_time
        while True:
            expire_time  = lease_time-(time-set_time)
            if expire_time == int(lease_time / 2):
                DHCPRequest(self.socket, self.DHCPOffer)
                # print(f"The client sent Request message on 50% of Lease-time for IP Address: {ip_address}")
            elif expire_time == int((lease_time) / 8):
                DHCPDiscover(self.socket, self.DHCPOffer.chaddr)
                # print(f"The client sent Discover message in 87.5% of Lease-time")

class AckTimeout(threading.Thread):
    def __init__(self, socket ,mac_address):
        threading.Thread.__init__(self)
        self.socket = socket
        self.mac_address = mac_address

    def run(self):
        global ack_timeout, ack_notfi
        sleep(ack_timeout)
        if ack_notfi == 1:
            ack_notfi = 0
        else:
            print("The client could not receive Ack message from the server therefore would have resent the discover message.")
            DHCPDiscover(self.socket, self.mac_address)
            print("\nThe client sent Discover message")
                

def DHCPDiscover(socket: socket, mac_address: str):
    sleep(0.25)
    packet = dhcpp.DHCPPacket.Discover(mac_address)
    socket.sendto(packet.asbytes, BROADCAST)

def DHCPRequest(socket: socket, DHCPOffer: dhcpp.DHCPPacket):
    sleep(0.25)
    packet = dhcpp.DHCPPacket(op="BOOTREQUEST", htype="ETHERNET", hlen=6, hops=0, xid=DHCPOffer.xid, secs=0, flags=32768, ciaddr=ipaddress.IPv4Address('0.0.0.0'), yiaddr=ipaddress.IPv4Address('0.0.0.0'), siaddr=ipaddress.IPv4Address('0.0.0.0'), giaddr=ipaddress.IPv4Address('0.0.0.0'), chaddr=DHCPOffer.chaddr, sname=b'', file=b'', options=dhcpo.OptionList([dhcpo.options.short_value_to_object(12, "Erfan_Laptop"), dhcpo.MessageType(code=53, length=1, data=b'\x03'),  dhcpo.End(code=255, length=0, data=b'')]))
    socket.sendto(packet.asbytes, BROADCAST)

def dhcp_process(UDPClientSocket: socket, mac_address: str):
    receiver = Receiver(UDPClientSocket)
    receiver.start()
    
    DHCPDiscover(UDPClientSocket, mac_address)
    print("The client sent Discover message")

    discover = Dicovering(UDPClientSocket, mac_address)
    discover.start()
    
    global received_msg_flag, received_msg

    while True:
        if received_msg_flag == 1:
            received_msg_flag = 0
            type_msg = int.from_bytes(received_msg.options.by_code(53).data, "big")
            if type_msg == 2:
                global lease_time
                lease_time = int.from_bytes(received_msg.options[1].data, "big")
                print(f"The client receive Offer message from Server with Lease-time: {lease_time}  -  IP Address: {received_msg.yiaddr}")
                DHCPRequest(UDPClientSocket, received_msg)
                offer = deepcopy(received_msg)
                print(f"The client sent Request message for IP Address: {received_msg.yiaddr}")
                ack_timeout = AckTimeout(UDPClientSocket, mac_address)
                ack_timeout.start()  

            if type_msg == 5:
                global ack_notfi
                ack_notfi = 1
                global ip_address, set_time , time
                ip_address = received_msg.yiaddr
                set_time = time
                release = releaseIP()
                release.start()
                renew = keepIP(UDPClientSocket, offer)
                renew.start()
                print(f"The client receive Ack message from Server with Lease-time: {lease_time}  -  IP Address: {ip_address}")
                print(f"\n--------IP Address: {ip_address}--------")
                
                

if __name__ == "__main__":

    UDPClientSocket = socket.socket( socket.AF_INET, socket.SOCK_DGRAM)
    UDPClientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    UDPClientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    UDPClientSocket.bind((IP_ADDRESS, PORT))

    mac_address = ':'.join(['{:02x}'.format((getnode() >> ele) & 0xff)for ele in range(0,8*6,8)][::-1])
    # mac_address = "00:0a:d2:a2:bc:46"
 
    timer= myTimer()
    timer.start()
 
    dhcp_process(UDPClientSocket, mac_address)
