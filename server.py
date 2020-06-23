import socket
import sys
import os
import threading
import _thread

class Server:
    def __init__(self, RFC_list = None, peer_list = None, server_socket = None, port = None):
        self.RFC_list = []
        self.peer_list = []
        self.port = 7734
        self.server_socket = socket.socket()         # Create a socket object
        host = socket.gethostname()             # Get local machine name
        self.server_socket.bind((host, self.port))        # Bind to the port

    def on_new_client(self, clientsocket,addr):
        while True:
            message = clientsocket.recv(1024).decode()
            print("Got connection from: " +  str(addr)) #confirm connection

            chopped_message = message.split()

            #if we haven't seen this client, add it to peer list
            if not "END" in message:
                for i in range(len(chopped_message)-1):
                    if "Port:" in chopped_message[i]:
                        #check peer list and add if not there
                        port_num = chopped_message[i+1]
                for i in range(len(chopped_message)-1):
                    if "Host:" in chopped_message[i]:
                        host_name = chopped_message[i+1]
                self.peer_list.append((host_name, port_num))
            else: #there is an end
                print("Trying to end")
                new_peer_list = []
                new_RFC_list = []
                for i in range(len(chopped_message)-1):
                    if "Port:" in chopped_message[i]:
                        #check peer list and add if not there
                        port_num = chopped_message[i+1]
                #clean peer list
                for i in self.peer_list:
                    if not port_num in i:
                        new_peer_list.append(i)
                #clean RFC list
                for i in self.RFC_list:
                    if not port_num in i:
                        new_RFC_list.append(i)
                self.RFC_list = new_RFC_list
                self.peer_list = new_peer_list
                clientsocket.close()
                sys.exit()

            #print(self.peer_list)
            if "ADD" in message:
                entry = []
                confirm_msg = "P2P-CI/1.0 200 OK\r\n\r\n"
                
                entry.append(int(chopped_message[2]))
                # Allows to have multiple entries of the same file
                for i in range(len(chopped_message)-1):
                    if "Title" in str(chopped_message[i]):
                        title = chopped_message[i+1]
                        entry.append(title)

                for i in range(len(chopped_message)-1):
                    if "Host" in str(chopped_message[i]):
                        host = chopped_message[i+1]
                        entry.append(host)
                
                for i in range(len(chopped_message)-1):
                    if "Port:" in chopped_message[i]:
                        #check peer list and add if not there
                        port_num = chopped_message[i+1]
                        entry.append(port_num)
                confirm_msg = confirm_msg + chopped_message[1] + " " + title + " " + host + " " + port_num + "\r\n\r\n"
                clientsocket.send(confirm_msg.encode())
                self.RFC_list.append(entry)
                #print(self.RFC_list)
            elif "LOOKUP" in message:
                #LOOKUP RFC 3457 P2P-CI/1.0
                #Host: thishost.csc.ncsu.edu
                #Port: 5678
                #Title: Requirements for IPsec Remote Access Scenarios

                lookup_message = "P2P-CI/1.0 "
                for i in self.RFC_list:
                    if int(message.split()[2]) == int(i[0]):
                        lookup_message = lookup_message + "200 OK\r\n\r\n"
                        lookup_message = lookup_message + str(i[0]) + " " + i[1] + " " + i[2] + " " + str(i[3]) + " " + socket.gethostbyname(i[2])+ "\r\n"
                        lookup_message = lookup_message + "\r\n"
                        clientsocket.send(lookup_message.encode())
                        return
                
                lookup_message = lookup_message + "404 Not Found\r\n\r\n"
                lookup_message = lookup_message + "N/A " + "N/A " + "N/A " + "N/A\r\n"
                lookup_message = lookup_message + "\r\n"
                clientsocket.send(lookup_message.encode())
                

            elif "LIST" in message:
                #version <sp> status code <sp> phrase <cr> <lf>
                #<cr> <lf>
                #RFC number <sp> RFC title <sp> hostname <sp> upload port number<cr><lf>
                #RFC number <sp> RFC title <sp> hostname <sp> upload port number<cr><lf>
                #...
                #<cr><lf>

                list_message = "P2P-CI/1.0 200 OK\r\n\r\n"
                for i in self.RFC_list:
                    print(socket.gethostbyname(i[2]))
                    list_message = list_message + str(i[0]) + " " + i[1] + " " + i[2] + " " + str(i[3]) + " " + socket.gethostbyname(i[2]) + "\r\n"
                list_message = list_message + "\r\n"
                clientsocket.send(list_message.encode())
            

            #clientsocket.send(message.encode())
        clientsocket.close()



def main():
    s = Server()
    try:
        s.server_socket.listen(5) 
        while True: #wait and listen
            (c, addr) = s.server_socket.accept()     # Establish connection with client.
            _thread.start_new_thread(s.on_new_client,(c,addr))
            
            
    except KeyboardInterrupt:
        s.server_socket.close()
        print("Done")
        sys.exit(0)
        pass
    
main()
