import socket

target_host = "localhost"
target_port = 5123

# create a socket object
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# connect the client
client.connect((target_host, target_port))

# send some data
client.send(b"GET / HTTP/1.1\r\nHost: www.google.com\r\n\r\n")

# receive data
response = client.recv(4096)

print(response)