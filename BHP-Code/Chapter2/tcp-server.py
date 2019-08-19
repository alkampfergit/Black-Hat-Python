import socket
import threading


def handle_client(client_socket):
    
    # send something
    client_socket.send(b"Connected\r\n")
    
    # print out what the client sends
    request = client_socket.recv(1024)
    
    print ("[*] Reveived: %s" % request)
    
    # send back a packet
    client_socket.send(b"ACK!\r\n")
    
    client_socket.close()

#This is the main function
bind_ip = "0.0.0.0"
bind_port = 5123

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind((bind_ip, bind_port))

server.listen(5)

print ("[*] Listening on %s:%d" % (bind_ip, bind_port))
    
while True:
    client, addr = server.accept()
    
    print ("[*] Accepted connection from: %s:%d" % (addr[0], addr[1]))
    
    # spin up our client thread to handle incoming data
    client_handler = threading.Thread(target=handle_client,args=(client,))
    client_handler.start()
