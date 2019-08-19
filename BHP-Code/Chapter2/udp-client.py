import socket

target_host = "127.0.0.1"
target_port = 80

# create a socket object
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#Changed in version 3 of python, need to bind to port.
client.bind((target_host, target_port))

# send some data
client.sendto(b"AAABBBCCC",(target_host, target_port))

# recieve some data
data, addr = client.recvfrom(4096)

print(data)