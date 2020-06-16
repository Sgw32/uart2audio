import socket
import time

HOST = '127.0.0.1'                 # Symbolic name meaning all available interfaces
PORT = 5050              # Arbitrary non-privileged port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
conn, addr = s.accept()
print 'Connected by', addr
temp = 0
while 1:
    temp+=1
    if (temp==40):
        temp=-40
    s="T1 " + str(temp) + " \x01"
    print s
    conn.sendall(s)
    s="H1 " + str(temp+70) + " \x01"
    print s
    conn.sendall(s)
    time.sleep(0.5)
conn.close()
