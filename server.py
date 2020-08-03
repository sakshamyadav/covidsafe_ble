#coding: utf-8
from socket import *
import sys
import threading
import time
import datetime as dt
import random
import json
#using the socket module

#Define connection (socket) parameters
#Address + Port no
#Server would be running on the same host as Client
# change this port number if required
serverPort = int(sys.argv[1])
delay = int(sys.argv[2])

clients = []
blocked = []
serverSocket = socket(AF_INET, SOCK_STREAM)
#This line creates the server’s socket. The first parameter indicates the address family; in particular,AF_INET indicates that the underlying network is using IPv4.The second parameter indicates that the socket is of type SOCK_STREAM,which means it is a TCP socket (rather than a UDP socket, where we use SOCK_DGRAM).
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind((gethostbyname(gethostname()), serverPort))
#The above line binds (that is, assigns) the port number 12000 to the server’s socket. In this manner, when anyone sends a packet to port 12000 at the IP address of the server (localhost in this case), that packet will be directed to this socket.
serverSocket.listen(1)

#The serverSocket then goes in the listen state to listen for client connection requests. 

def unblock(username):
    time.sleep(delay)
    blocked.remove(username)


def recv(connectionSocket, addr): 

#When a client knocks on this door, the program invokes the accept( ) method for serverSocket, which creates a new socket in the server, called connectionSocket, dedicated to this particular client. The client and server then complete the handshaking, creating a TCP connection between the client’s clientSocket and the server’s connectionSocket. With the TCP connection established, the client and server can now send bytes to each other over the connection. With TCP, all bytes sent from one side not are not only guaranteed to arrive at the other side but also guaranteed to arrive in order
    username = connectionSocket.recv(1024)
    username = username.decode()

    if username in blocked: 
        connectionSocket.send('blocked'.encode())
        connectionSocket.close()
        sys.exit()
    else:
        connectionSocket.send('proceed'.encode())

    count = 0 
    success = 0 
    while count < 3 and not success: 
        password = connectionSocket.recv(1024)
        password = password.decode()
    #wait for data to arrive from the client
        
        for l in open('credentials.txt', 'r').readlines():
            user_pass = l.split()
            if username == user_pass[0] and password == user_pass[1]:
                connectionSocket.send("success".encode())
                success = 1
                clients.append(username)
                break    
        if not success:   
            connectionSocket.send("failed".encode())
            count +=1 

    if success:

        while True:
            command = connectionSocket.recv(1024)
            command = command.decode() 

            if command == 'Download_tempID':
                currtime = dt.datetime.now()
                expiry_time = currtime + dt.timedelta(minutes=15)
                currtime = currtime.strftime("%d/%m/%Y %H:%M:%S").encode('ascii').decode()
                expiry_time = expiry_time.strftime("%d/%m/%Y %H:%M:%S").encode('ascii').decode()
                temp_id = str(random.randint(10**19, (10**20)-1)).encode('ascii').decode()
                append_str = username+' '+temp_id+' '+currtime+' '+expiry_time
                f = open("tempIDs.txt", "a+")
                f.write(append_str+'\n')
                f.close()
                version_num = '1'
                tempid_details = [temp_id, currtime, expiry_time, version_num]
                tempid_details = json.dumps({"temp_details":tempid_details})
                connectionSocket.send(tempid_details.encode())
                print('user:', username)
                print('TempID:', temp_id,'\n')

            elif command == 'Upload_contact_log':
                print("received contact log from", username)
                contact_tempID = []
                contact_users = []
                #output contact log
                contact_log = connectionSocket.recv(4096)
                contact_log = json.loads(contact_log.decode('ascii'))
                contact_log = contact_log.get('log_details')
                for log in contact_log:
                    log = log.split()
                    print(log[0]+', '+log[1]+' '+log[2]+', '+log[3]+' '+log[4]+';')
                    contact_tempID.append(log[0])

                print("")
                #tracing
                print("Contact log checking")
                f = open("tempIDs.txt", "r")
                lines = f.readlines()
                for line in lines: 
                    line = line.split()
                    if line[1] in contact_tempID:
                        contact_users.append((line[0], line[2], line[3], line[1]))
                f.close()
                for users in contact_users:
                    print(users[0]+', '+users[1]+' '+users[2]+', '+users[3]+';')
                print("")

            elif command == 'logout':
                clients.remove(username)
                print(username, 'logout')
                connectionSocket.close()
                sys.exit()

    else:
        blocked.append(username)
        threading.Thread(target=unblock, args=(username,)).start()
        
    connectionSocket.close()
    sys.exit()
    
while True:
    print("The server is ready to receive")
    connectionSocket, addr = serverSocket.accept()
    print(addr)
    threading.Thread(target=recv, args = (connectionSocket,addr,)).start()


connectionSocket.close()

#change the case of the message received from client

#and send it back to client

#close the connectionSocket. Note that the serverSocket is still alive waiting for new clients to connect, we are only closing the connectionSocket.