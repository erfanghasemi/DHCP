def increase_ip(ip):
    ip = ip.split('.')
    ip[3] = str(int(ip[3]) + 1)
    if ip[3] == "256":
        ip[3] = "0"
        ip[2] = str(int(ip[2]) + 1)
    ip = ".".join(ip)
    return ip

def create_IP_range(start, stop, mode):
    ip_list = []

    if mode == "range":    
        ip_list.append(start)

        current_ip = start
        while current_ip != stop:
            current_ip = increase_ip(current_ip)
            ip_list.append(current_ip)
        
    elif mode == "subnet":
        ip_block = start
        subnet_mask = stop

        subnet_mask = subnet_mask.split('.')
        ip_block = ip_block.split('.')

        for i in range(len(subnet_mask)):
            subnet_mask[i] = format(int(subnet_mask[i]),'08b')
            ip_block[i] = format(int(ip_block[i]),'08b')

        subnet_mask = ''.join(subnet_mask)
        ip_block = list(''.join(ip_block))
        ip_block[32-subnet_mask.count('0'):] = subnet_mask.count('0')*['0']
        network_address = str(int(''.join(ip_block[:8]), 2))+"."+str(int(''.join(ip_block[8:16]), 2))+"."+str(int(''.join(ip_block[16:24]), 2))+"."+str(int(''.join(ip_block[24:]), 2))
        network_size = pow(2, subnet_mask.count('0')) - 2        
        
        for i in range(network_size):
            network_address = increase_ip(network_address)
            ip_list.append(network_address)
    
    return ip_list

    