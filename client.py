#coding: utf-8
from socket import *
import sys
import threading
import multiprocessing as mp
import json
import datetime as dt
import time
#Define connection (socket) parameters
#Address + Port no
#Server would be running on the same host as Client
serverName = sys.argv[1]

#change this port number if required
serverPort = int(sys.argv[2])

udpPort = int(sys.argv[3])
udpIP = gethostbyname(gethostname())

clientSocket = socket(AF_INET, SOCK_STREAM)
#This line creates the client’s socket. The first parameter indicates the address family; in particular,AF_INET indicates that the underlying network is using IPv4. The second parameter indicates that the socket is of type SOCK_STREAM,which means it is a TCP socket (rather than a UDP socket, where we use SOCK_DGRAM). 

clientSocket.connect((serverName, serverPort))
#Before the client can send data to the server (or vice versa) using a TCP socket, a TCP connection must first be established between the client and server. The above line initiates the TCP connection between the client and server. The parameter of the connect( ) method is the address of the server side of the connection. After this line of code is executed, the three-way handshake is performed and a TCP connection is established between the client and server.
p2pSocket = socket(AF_INET, SOCK_DGRAM)
p2pSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
p2pSocket.bind((udpIP, udpPort)) 

def remove_expired_beacons():
	time.sleep(180)
	f = open("z5164624_contactlog.txt", "r")
	lines = f.readlines()
	f.close()

	del lines[0]

	f = open("z5164624_contactlog.txt", "w+")

	for line in lines:
		f.write(line)
	f.close()
	sys.exit()




def listen():
	while True: 
		beacon, addr = p2pSocket.recvfrom(1024)
		beacon = json.loads(beacon.decode('ascii'))
		beacon = beacon.get('temp_details')
		beacon_tempID = beacon[0]
		beacon_tempID_start = beacon[1]
		beacon_tempID_expiry = beacon[2]
		version_num = beacon[3]

		currtime = dt.datetime.now()
		currtime_str = currtime.strftime("%d/%m/%Y %H:%M:%S").encode('ascii').decode()
		start_time = dt.datetime.strptime(beacon_tempID_start, "%d/%m/%Y %H:%M:%S")
		expiry_time = dt.datetime.strptime(beacon_tempID_expiry, "%d/%m/%Y %H:%M:%S")

		print('received beacon: '+beacon_tempID+', '+beacon_tempID_start+', '+beacon_tempID_expiry+'.')
		print('Current time is: '+currtime_str+'.')

		if currtime >= start_time and currtime <= expiry_time:
			print("The beacon is valid.")
			append_str = beacon_tempID+' '+beacon_tempID_start+' '+beacon_tempID_expiry+' '+version_num
			f = open("z5164624_contactlog.txt", "a+")
			f.write(append_str+'\n')
			mp.Process(target = remove_expired_beacons).start()
			f.close()
		else:
			print("The beacon is invalid.")

		print('>', end='', flush=True)

username = input('Username: ')
username = username.encode()

clientSocket.sendto(username, (serverName,serverPort))

response = clientSocket.recv(1024)
response = response.decode()

if response == 'blocked':
	print("Your account is blocked due to multiple login failures. Please try again later")
	sys.exit()

counter = 0 
success = 0
#We wait to receive the reply from the server, store it in modifiedSentence
while counter < 3 and not success: 

	password = input('Password: ')
	password = password.encode()

	clientSocket.sendto(password, (serverName, serverPort))

	response = clientSocket.recv(1024)
	response = response.decode()

	if response == 'success':
		success = 1 
		listen_thread = mp.Process(target=listen)
		listen_thread.start() 
		break
	elif counter != 2:
		print("Invalid Password. Please try again")
	
	counter+=1

if success:
	print('Welcome to the BlueTrace Simulator!')

	while True:
		command = input('>')
		if command == 'Download_tempID':
			command = command.encode()
			clientSocket.sendto(command, (serverName, serverPort))
			tempid_details = clientSocket.recv(1024)
			tempid_details = json.loads(tempid_details.decode('ascii')) 
			tempid_details = tempid_details.get('temp_details')
			print('TempID:', tempid_details[0])

		elif command == 'Upload_contact_log':
			command = command.encode()
			clientSocket.sendto(command, (serverName, serverPort)) 
			f = open("z5164624_contactlog.txt", 'r')
			lines = f.readlines()
			for line in lines: 
				line = line.split()
				print(line[0]+', '+line[1]+', '+line[2]+';')

			lines = json.dumps({"log_details":lines})
			clientSocket.sendto(lines.encode(), (serverName, serverPort))
			f.close()

		elif 'Beacon' in command:
			args = command.split()
			dest_IP = args[1]
			dest_port = int(args[2])
			print(tempid_details[0]+', '+tempid_details[1]+', '+tempid_details[2]+'.')
			send_beacon = json.dumps({"temp_details":tempid_details})
			p2pSocket.sendto(send_beacon.encode(), (dest_IP, dest_port))

		elif command == 'logout':
			command = command.encode()
			clientSocket.sendto(command, (serverName, serverPort))
			clientSocket.close()
			listen_thread.terminate()
			sys.exit()

		else:
			print("Error. Invalid command")

else:
	print("Invalid Password. Your account has been blocked. Please try again later")

#close the clientSocket
clientSocket.close()

