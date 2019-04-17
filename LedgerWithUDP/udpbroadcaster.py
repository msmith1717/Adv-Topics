import time
import socket
import threading
import random
import json
import signal
import sys

import requests
import encrypt

from peer import Peer

"""
Represents the our UDP broadcaster and receiver
Attributes:
    peerlist: a shared list of known peers
    lock: a shared lock to assure mutual exclusion for the peer list
    serverWallet: the wallet for the server (used for nonce encryption)
    localIP: our current exposed IP address
    receiving: flag to tell the server to shutdown
"""
class UDPBroadcaster:

    RECEIVE_PORT = 5001     # listen on this port for UDP packets
    BROADCAST_DELAY = 3     # delay between each broadcast (in seconds)


    def __init__(self, serverWallet, peerlist, lock):
        self.peerlist = peerlist
        self.lock = lock
        self.serverWallet = serverWallet
        self.localIP = socket.gethostbyname(socket.gethostname())

        self.receiving = True

    def broadcast(self):
        print('Starting Broadcaster...')

        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        message = {'coin':'simplecoin', 'id':self.serverWallet.public}
        message = json.dumps(message).encode()

        # Constrantly broadcast until we need to shutdown
        while self.receiving:
            time.sleep(UDPBroadcaster.BROADCAST_DELAY)
            client.sendto(message, ('<broadcast>', UDPBroadcaster.RECEIVE_PORT))

        print('UDP Client Thread Exiting...')

    def receive(self):
        print('Starting Receiver...')

        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        server.bind(('', UDPBroadcaster.RECEIVE_PORT))
        server.settimeout(3)

        while self.receiving:
            try:

                # block until we pick up a broadcast packet
                data, addr = server.recvfrom(2048)
                data = json.loads(data)      

                # Create a communication nonce
                sendNonce = random.randint(100000, 1000000000)
                ipNonce = dict()
                ipNonce['address'] = addr
                ipNonce['nonce'] = sendNonce

                ipNonce = json.dumps(ipNonce)
                ipNonce = encrypt.encryptWithKey(data['id'], ipNonce)

                """
                 Setup data to send
                  data -- the address and nonce
                  id -- our public key
                """
                sendData = dict()
                sendData['data'] = ipNonce
                sendData['id'] = self.serverWallet.public

                # Send a post request and pull a JSON from the return
                URL = 'http://'+addr[0]+':5000/peer'
                rtnData = requests.post(URL, json=sendData).json()

                # Get the peers and decrypt the nonce
                rtnPeers = rtnData['peers']
                rtnPeer = Peer.parseJSON(rtnData['id'])
                rtnNonce = int(encrypt.decryptWithKey(rtnPeer.publicKey, rtnData['nonce']))

                # Grab the lock, check the nonce and add the peers to our list
                self.lock.acquire()
                if rtnNonce == sendNonce:
                    for peer in rtnPeers:
                        key = peer['ip']+':'+str(peer['port'])
                        if key not in self.peerlist:
                            self.peerlist[key] = Peer(peer['publicKey'], peer['ip'], peer['port'], peer['nonce'])
                self.lock.release()

            except Exception as e:
                # Make sure the lock is released so we can't deadlock
                if self.lock.locked():
                    self.lock.release()
                pass

        print('UDP Server Thread Exiting...')

    def shutdown(self):
        self.receiving = False

    """
        Run the UDP server.  We launch two threads so that the 
        broadcaster and receiver can run simultaneously
    """
    def run(self):
        print('Starting UDP Communication...')
        print('Press Ctrl-C to exit.\n')
        broadcaster = threading.Thread(target=self.broadcast)
        receiver = threading.Thread(target=self.receive)
        
        receiver.start()
        broadcaster.start()

        receiver.join()
        broadcaster.join()
        print('UDP Server Shutdown Complete', flush=True)
        

if __name__ == '__main__':
    peerlist = []
    lock = threading.Lock()

    broadcaster = UDPBroadcaster(peerlist, lock)

    # Setup a clean shutdown of the server
    def shutdown(sig, frame):
        print('\b\b  ')                     # Delete the ^C on terminal
        print('Shutting Down. Please wait...')
        broadcaster.shutdown()

    # Handle the Ctrl-C
    signal.signal(signal.SIGINT, shutdown )

    broadcaster.run()