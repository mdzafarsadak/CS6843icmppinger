
#Mdzafar Sadak
#Spring2021
from socket import *
import os
import sys
import struct
import time
import select
import binascii
import math
ICMP_ECHO_REQUEST = 8
def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0
    while count < countTo:
        thisVal = (string[count + 1]) * 256 + (string[count])
        csum += thisVal
        csum &= 0xffffffff
        count += 2

    if countTo < len(string):
        csum += (string[len(string) - 1])
        csum &= 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def receiveOnePing(mySocket, ID, timeout, destAddr):
    timeLeft = timeout

    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []:  # Timeout
            return "Request timed out."

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        icmp = recPacket[20:28]
        type, code, checksum, ID_recv, sq = struct.unpack('bbHHh', icmp)
        data = struct.calcsize('d')
        sent = struct.unpack('d', recPacket[28:28 + data])[0]
        rtt = timeReceived - sent
        return rtt * 1000

        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return "Request timed out."


def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)

    myChecksum = 0
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(header + data)

    if sys.platform == 'darwin':
        # Convert 16-bit integers from host to network  byte order
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data

    mySocket.sendto(packet, (destAddr, 1))  # AF_INET address must be tuple, not str

def doOnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")

    # SOCK_RAW is a powerful socket type. For more details:   http://sockraw.org/papers/sock_raw
    mySocket = socket(AF_INET, SOCK_RAW, icmp)

    myID = os.getpid() & 0xFFFF  # Return the current process i
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
    mySocket.close()
    return delay


def packet_min(delays):
    return min(delays)


def packet_max(delays):
    return max(delays)


def packet_avg(delays):
    return (sum(delays) / len(delays))


def stdev_var(delays):
    vart = sum(pow(i - (sum(delays) / len(delays)), 2) for i in delays) / len(delays)
    return math.sqrt(vart)


def ping(host, timeout=1):
    # timeout=1 means: If one second goes by without a reply from the server,      # the client assumes that either the client's ping or the server's pong is lost
    dest = gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    print("")
    # Calculate vars values and return them

    delays = []
    # Send ping requests to a server separated by approximately one second
    for i in range(0, 4):
        delay = doOnePing(dest, timeout)
        print(delay)
        time.sleep(1)  # one second
        delays.append(delay)
    vars = [str(round(packet_min(delays), 2)), str(round(packet_avg(delays), 2)), str(round(packet_max(delays), 2)),
            str(round(stdev_var(delays), 2))]
    return vars


if __name__ == '__main__':
    ping("google.co.il")
