from __future__ import print_function
import sys

# Python Version Check
if sys.version_info < (3,5):
    print('Python version detected: ' + str(sys.version_info[0]) + '.'+str(sys.version_info[1]))
    print('Python version required: 3.5 or higher')
    sys.exit(1)

# Version check passed. Complete imports
import os.path
import json
import threading
import signal
import socket
import random

from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify

import blockchain
import encrypt as RSA
import keygen
import udpbroadcaster
from peer import Peer


LEDGER_PORT = 5000

# Initialize the System Wallet and main BlockChain
print('Loading BlockChain System keys...')
if not os.path.isfile('./System_private.key') or not os.path.isfile('./System_public.key'):
    print('FATAL: System keys not found. Exiting...')
    sys.exit(-1)


system_public = RSA.load('System_public.key')
system_private = RSA.load('System_private.key')
systemWallet = blockchain.Wallet('Creator', system_public, system_private)
MainChain = blockchain.BlockChain(systemWallet)


# Load the Server keys; If they don't exist, then generate them
print('Loading Server keys...')
if not os.path.isfile('./Server_private.key') or not os.path.isfile('./Server_public.key'):
    print('Server keys not found. Regenerating them...', end='', flush=True)
    keygen.generate_keys('Server')
    print('Done.')

server_public = RSA.load('Server_public.key')
server_private = RSA.load('Server_private.key')
serverWallet = blockchain.Wallet('Server', server_public, server_private)

# Shared list of peers and the lock to assure mutual exclusion
peerList = dict()
peerLock = threading.Lock()

# Setup the UDP Broadcaster and pass in the shared list and lock
udpCaster = udpbroadcaster.UDPBroadcaster(serverWallet, peerList, peerLock)

# flask server
app = Flask(__name__)
app.config['ENV'] = 'development'

@app.route('/transactions', methods=['POST'])
def addTransactions(transactions=[]):
    try:
        transactionsJSON = request.get_json()
        transactions = []
        
        for transaction in transactionsJSON['transactions']:
            trans = blockchain.Transaction.parseJSON(transaction)
            transactions.append(trans)

        MainChain.mineBlock(transactions)
        return jsonify({'status':'ok', 'numAccepted':len(transactions)})
        
    except RuntimeError:
        pass

    return jsonify({'status':'error'})

@app.route('/transactions/<blockID>', methods=['GET'])
def get_block(blockID, mode='html'):

    blockID = int(blockID)-1;
    it = MainChain.iterator(blockID)
    try:
        block = next(it);
        return render_template('displayblocks.html', blocks=[block])
    except StopIteration:
        return "Block {} does not exist".format(blockID+1)



@app.route('/transactions', methods=["GET"])
def get_blocks(start=0, mode='html'):

    # Handle start GET argument
    # We might be outside the Request context
    try:
        s = request.args.get('start')
        if s != None:
            s = int(s)
            if s >= 1:
                start = int(s) - 1
    except RuntimeError:
        pass

    blocks = []
    it = MainChain.iterator(start)
    for block in it:
        blocks.append(block)

    return render_template('displayblocks.html', blocks=blocks)

@app.route('/peers', methods=['GET'])
def get_peers(mode='html'):

    # handle the mode parameter to the route
    try:
        mode = request.args.get('mode')
    except RuntimeError:
        pass

    # Grab the lock so that we can generate the data to return
    peerLock.acquire()
    if mode == 'json':
        peerRtn = json.dumps(peerList, cls=blockchain.ChainEncoder)
    else:
        peerRtn = render_template('displaypeers.html', peers=peerList )
    peerLock.release()
    return peerRtn

@app.route('/peer', methods=['POST'])
def addPeers():

    nonce = 0
    try:
        peersJSON = request.get_json()

        # load up the data
        data = RSA.decryptWithKey(serverWallet.private, peersJSON['data'])
        data = json.loads(data)
        
        peer = Peer(peersJSON['id'], data['address'][0], data['address'][1], data['nonce'])
        key = peer.ip+':'+str(peer.port)

        # Grab the lock so that we can copy the peer list for returning
        rtnPeers = []
        peerLock.acquire()
        if key not in peerList:
            for key, sendPeer in peerList.items():
                rtnPeers.append(sendPeer.toJSON())
            peerList[key] = peer
        peerLock.release()

        # generate a nonce for communicating with me
        myIP = socket.gethostbyname(socket.gethostname())
        meNonce = random.randint(1000000, 1000000000)
        meNonce = RSA.encryptWithKey(serverWallet.private, str(meNonce))
        me = Peer(serverWallet.public, myIP, LEDGER_PORT, meNonce)

        rtn = {
            "peers": rtnPeers,
            "id": me.toJSON(),
            "nonce": RSA.encryptWithKey(serverWallet.private, str(peer.nonce))
        }
        return json.dumps(rtn)
    except Exception as e:
        # An exception happened, so we need to make sure the lock is released!
        if peerLock.locked():
            peerLock.release()
        pass 

    return "ERROR"


# Do a clean shutdown of all the threads we created
def server_shutdown(sig, frame):
    print("\b\bServer Shutting Down. Please Wait...", flush=True)
    if peerLock.locked():
        peerLock.release()
    udpCaster.shutdown()

# Startup the server
def server_startup():

    # Spin up two threads: UDP and HTTP
    UDPThread = threading.Thread(target=udpCaster.run)
    HTTPThread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=LEDGER_PORT) )
    HTTPThread.setDaemon(True)

    # Setup a handler for Ctrl-C so that we can clean up correctly
    signal.signal(signal.SIGINT, server_shutdown)
    HTTPThread.start()
    UDPThread.start()

    UDPThread.join()
    print("Server Shutdown Complete")

if __name__ == '__main__':
    server_startup()