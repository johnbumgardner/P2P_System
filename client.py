import socket               # Import socket module
import os
import sys
import platform
import _thread
from datetime import datetime
import re
import time

class Client:
	def __init__(self, RFC_list = None, socket_for_server = None, upload_socket = None):
		self.RFC_list = []	#contains the RFC files a client has
		arr = os.listdir()
		for x in arr:
			if ".txt" in x:
				self.RFC_list.append(x)
		self.socket_for_server = socket.socket()
		host = socket.gethostname() # Get local machine name
		port = 7734               # Reserve a port for your service.
		self.socket_for_server.connect(('192.168.1.159', port))

		#define a UDP socket to handle the P2P communications
		self.upload_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.upload_socket.bind((host, 0))

	def add_to_server_db(self,file_name):
		RFC_num = ''.join(i for i in file_name if i.isdigit())
		request1 = "ADD RFC " + str(RFC_num) + " P2P-CI/1.0\r" 
		request2 = "\nHost: " + socket.gethostname() + "\r\n"
		request3 = "Port: " + str(self.upload_socket.getsockname()[1]) + "\r\n\r"
		request4 = "Title: " + file_name + "\r\n\r"
		request5 = "\n"

		request = request1 + request2 + request3 + request4 + request5
		print(request)
		
		self.socket_for_server.send(request.encode())
		

	def lookup(self, file_name):
		RFC_num = ''.join(i for i in file_name if i.isdigit())
		request1 = "LOOKUP RFC " + str(RFC_num) + " P2P-CI/1.0\r" 
		request2 = "\nHost: " + socket.gethostname() + "\r\n"
		request3 = "Port: " + str(self.upload_socket.getsockname()[1]) + "\r\n\r"
		request4 = "Title: " + file_name + "\r\n\r"
		request5 = "\n"

		request = request1 + request2 + request3 + request4 + request5
		print(request)
		
		self.socket_for_server.send(request.encode())
		


	def list(self, file_name):
		request1 = "LIST ALL P2P-CI/1.0\r" 
		request2 = "\nHost: " + socket.gethostname() + "\r\n"
		request3 = "Port: " + str(self.upload_socket.getsockname()[1]) + "\r\n\r"
		request4 = "\n"

		request = request1 + request2 + request3 + request4
		print(request)
		print(request.encode)
		self.socket_for_server.send(request.encode())
		
	def end(self, cmd):
		request1 = "END P2P-CI/1.0\r" 
		request2 = "\nHost: " + socket.gethostname() + "\r\n"
		request3 = "Port: " + str(self.upload_socket.getsockname()[1]) + "\r\n\r"
		request4 = "\n"
		request = request1 + request2 + request3 + request4
		self.socket_for_server.send(request.encode())
		self.socket_for_server.close()
		
	def get(self, command):
		command = command.split()
		file_name = command[1]
		ip_addr = command[2]
		port_num = command[3]

		socket_info = ('' + ip_addr , int(port_num))
		print(socket_info)
		RFC_num = ''.join(i for i in file_name if i.isdigit())
		get_request = "GET RFC" + str(RFC_num) + " P2P-CI/1.0\r\n"
		get_request = get_request + "Host: " + ip_addr + "\r\n"
		get_request = get_request + "OS: " + platform.system() + " " + platform.release()



		to_peer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		to_peer_socket.connect(socket_info)
		to_peer_socket.send(get_request.encode())
		
		(number_of_packets, serverAddress) = to_peer_socket.recvfrom(65535)
		to_listen = number_of_packets.decode()
		print(to_listen)
		#to_peer_socket.close()

		packets_received = 0
		total_file_contents = ""
		while packets_received < int(to_listen):
			(packet, serverAddress) = to_peer_socket.recvfrom(65535)
			total_file_contents = total_file_contents + (packet.decode()[150:])

			packets_received = packets_received + 1


		#self.end("text")		
		if "404" in total_file_contents:
			print("404 Error: FIle Not Found")
		else:
			f = open(file_name, "w")
			f.write(total_file_contents)
			f.close()

		return



def listen_to_upload_port(client, x):
	#version <sp> status code <sp> phrase <cr> 
	#<lf> header field name <sp> value <cr> <lf> 
	#header field name <sp> value <cr> <lf> ...
	#<cr> <lf>
	#data

		while True:
			(request, addr) = client.upload_socket.recvfrom(1024)
			request = request.decode()
			file_name = request.split()[1]+".txt"
			
			now = datetime.now()
			date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
			#see if file name is held in the directory
			files = os.listdir() #list of files in directory
			file_found = 0
			for name in files:
				if file_name == name:
					file_found = 1
			if file_found:		
				file_object = open(file_name, 'r')
				data = file_object.read()
				packets = get_data_packets(data, 2048)
				num_packets = len(packets)
				print("Packet Num "  + str(num_packets))

				#send the peer the number of packets to expect
				client.upload_socket.sendto(str(num_packets).encode(), addr)

				for i in packets:
					message = "P2P-CI/1.0 200 OK\r\n"
					message = message + "Date: " + date_time + "\r\n"
					message = message + "OS: " +  platform.system() + " " + platform.release() + "\r\n"
					time = os.path.getmtime(file_name)
					message = message + "Last-Modified: " + str(time) + "\r\n"
					size = os.path.getsize(file_name)
					message = message + "Content-Length: " + str(size) + "\r\n"
					message = message + "Content-Type: text/text\r\n" 
					message = message + "\r\n" + i
					#print(message)
					client.upload_socket.sendto(message.encode(), addr)
				return
			else:
				message = "P2P-CI/1.0 404 NOT FOUND\r\n"
				message = message + "Date: " + date_time + "\r\n"
				message = message + "OS: " +  platform.system() + " " + platform.release() + "\r\n"
				#time = os.path.getmtime(file_name)
				message = message + "Last-Modified: N/A" + "\r\n"
				#size = os.path.getsize(file_name)
				message = message + "Content-Length: N/A" +  "\r\n"
				message = message + "Content-Type: N/A\r\n" 
				#message = message + "\r\n" + data
				#print(message)
				client.upload_socket.sendto(message.encode(), addr)
				return

def get_data_packets(data, size):
	#accepts the data from the file and divide up using regex
	m = re.compile(r'.{%s}|.+' % str(size),re.S)
	return m.findall(data)


def main():
	c = Client()
	_thread.start_new_thread(listen_to_upload_port, (c,0))
	
	try:
		while True:
			user_input = input("$")
			valid_in = 0
			if "ADD" in user_input:
				valid_in = 1
				file_name = user_input.replace("ADD ", "")
				c.add_to_server_db(file_name)
				#print(c.socket_for_server.recv(1024).decode)
			elif "LOOKUP" in user_input:
				valid_in = 1
				file_name = user_input.replace("LOOKUP ", "")
				c.lookup(file_name)
			elif "LIST" in user_input:
				valid_in = 1
				c.list("LIST")
			elif "END" in user_input:
				valid_in = 0
				c.end("END")
				print("Done")
				c.socket_for_server.close()
				sys.exit(0)
				pass
			elif "GET" in user_input:
				valid_in = 2
				c.get(user_input)
				print("Made it here")
			elif "HELP" in user_input:
				valid_in = 0
				print("Valid Inputs:\nADD <RFCfile>\nLOOKUP <RFCfile>\nLIST\nEND\nGET <RFCfile> <host name> <port number>")
			elif "INFO" in user_input:
				print("Host Name: " + str(socket.gethostname()))
				print("Port Number: " +str(c.upload_socket.getsockname()[1]))
			else:
				valid_in = 0
				print("Invalid Input: Type HELP for list of valid commands")
			
			if	valid_in == 1:
				print(c.socket_for_server.recv(1024).decode())
			elif valid_in == 2:
				print("File Written")
	except KeyboardInterrupt:
		c.socket_for_server.close()                     # Close the socket when done
		print("Done")
		sys.exit(0)
		pass
	
	
	


main()